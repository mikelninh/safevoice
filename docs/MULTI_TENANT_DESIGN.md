# Multi-Tenant Design — Sprint 1

**Goal:** NGOs like HateAid, Victim Support, or regional state-level victim counselling services can deploy SafeVoice as a team tool without data bleeding between orgs.

**Status:** design doc. Implementation in Sprint 1 (target Apr 21 — May 31).

## Requirements

1. **One deployment serves N orgs** (SaaS model for NGOs)
2. **Each org sees only its own data** (strict tenant isolation)
3. **Users can belong to multiple orgs** (a lawyer might work with HateAid + Weißer Ring)
4. **Role-based access within an org** (admin, caseworker, viewer)
5. **Org-level export** (all cases, CSV/ZIP for handover)
6. **Anonymous / individual-user mode still works** (a victim using SafeVoice solo shouldn't need to join an org)

## Entities

New tables:

```
orgs
├── id (uuid)
├── slug (unique, for URLs: hateaid, weisser-ring)
├── display_name
├── contact_email
├── created_at
├── settings_json  (org-level config: default language, PDF letterhead URL, etc.)
└── status (active/suspended/deleted)

org_members
├── user_id  FK → users
├── org_id   FK → orgs
├── role     enum: owner | admin | caseworker | viewer
├── joined_at
└── PRIMARY KEY (user_id, org_id)
```

Modifications to existing tables:

```
cases
+ org_id  FK → orgs  (nullable for individual cases, non-null for org cases)
+ assigned_to  FK → users  (which caseworker is handling it)
+ visibility  enum: private (just creator) | org (all members)
```

## Case Ownership Matrix

| Scenario | user_id | org_id | visibility | Who can read |
|----------|---------|--------|-----------|--------------|
| Individual victim, solo use | user_A | NULL | private | Only user_A |
| Victim uploads to HateAid | user_A | HateAid | private | user_A + HateAid admins |
| HateAid caseworker opens case | caseworker | HateAid | org | All HateAid members |
| Victim deletes account | NULL (user hard-deleted) | HateAid | private → org | HateAid keeps the case (legitimate interest in ongoing legal) |

**The hard question: what happens to an org case when the originating user deletes their account?**

**Proposal:** Option A (recommended) — case is transferred to org ownership with victim identity stripped (email, display_name nulled; the case content stays as evidence). The org keeps investigating but loses the ability to contact the victim. This aligns with DSGVO erasure (Art. 17(3)(b) — legitimate interests for legal claims).

## Role Permissions

| Action | owner | admin | caseworker | viewer |
|--------|-------|-------|------------|--------|
| Create case | ✓ | ✓ | ✓ | — |
| View org case | ✓ | ✓ | ✓ | ✓ |
| Update case | ✓ | ✓ | ✓ (assigned only) | — |
| Delete case | ✓ | ✓ | — | — |
| Export case | ✓ | ✓ | ✓ | ✓ |
| Bulk export all org cases | ✓ | ✓ | — | — |
| Add/remove members | ✓ | ✓ | — | — |
| Change member roles | ✓ | — | — | — |
| Delete org | ✓ | — | — | — |

## API Changes

New endpoints:

```
POST   /orgs                              Create org (requires authenticated user)
GET    /orgs                              List orgs user belongs to
GET    /orgs/{slug}                       Org detail
PUT    /orgs/{slug}                       Update org settings
DELETE /orgs/{slug}                       Delete org (owner only)

GET    /orgs/{slug}/members               List members
POST   /orgs/{slug}/members               Invite user by email
PUT    /orgs/{slug}/members/{user_id}     Change role
DELETE /orgs/{slug}/members/{user_id}     Remove member

GET    /orgs/{slug}/cases                 List org's cases (paginated)
POST   /orgs/{slug}/cases                 Create case in org
```

Modified existing endpoints:

```
GET /cases/                    Returns cases where user is owner OR org member
GET /cases/{id}                Authorization check: user owns OR is member of case.org
POST /cases/{id}/evidence      Authorization check: same + role allows update
```

## Authorization Pattern

Add a dependency:

```python
# app/services/authz.py

def require_case_access(
    case_id: str,
    db: Session,
    user: User,
    *,
    action: Literal["read", "write", "delete", "export"],
) -> Case:
    """Load the case and verify the user has permission for the action."""
    case = db.query(Case).filter_by(id=case_id).first()
    if not case:
        raise HTTPException(404)

    # Owner always has full access
    if case.user_id == user.id:
        return case

    # Org member access
    if case.org_id:
        membership = db.query(OrgMember).filter_by(
            user_id=user.id, org_id=case.org_id
        ).first()
        if not membership:
            raise HTTPException(403, "Not a member of this case's organization")

        required = _role_for_action(action)  # 'viewer', 'caseworker', 'admin', 'owner'
        if not _role_meets(membership.role, required):
            raise HTTPException(403, f"Role '{membership.role}' cannot {action}")

        return case

    raise HTTPException(403)
```

Use in routes:

```python
@router.get("/cases/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    case = require_case_access(case_id, db, user, action="read")
    return _case_to_response(case)
```

## Migration Plan

Alembic migration sequence (run in order):

1. **`0001_create_orgs`** — add `orgs` and `org_members` tables
2. **`0002_add_org_to_cases`** — add `cases.org_id`, `cases.assigned_to`, `cases.visibility` columns (all nullable)
3. **`0003_backfill_visibility`** — set `visibility='private'` for all existing cases
4. **`0004_constrain_case_ownership`** — add CHECK constraint: `user_id IS NOT NULL OR org_id IS NOT NULL`

Current existing cases: `user_id` might be NULL (anonymous). These stay — the CHECK constraint only applies to new rows. (Or: backfill anonymous cases to a synthetic "anonymous" user.)

## Row-Level Security (Supabase path)

If we adopt Supabase for auth (see `SUPABASE_AUTH.md`), we get RLS for free:

```sql
-- Enable RLS on cases
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

-- User can read their own cases
CREATE POLICY cases_own ON cases
  FOR SELECT USING (user_id = auth.uid());

-- User can read cases of orgs they belong to
CREATE POLICY cases_org_read ON cases
  FOR SELECT USING (
    org_id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid())
  );

-- Plus per-action policies for INSERT/UPDATE/DELETE with role checks...
```

RLS enforces at the DB layer — even if an API bug leaks `case_id`s across tenants, the DB refuses to return rows that don't pass the policy. Defense in depth.

## UI Changes (Sprint 1)

New screens:
- **Org switcher** in the top nav (when user belongs to ≥ 2 orgs)
- **Org dashboard** (members, cases, settings)
- **Invite member** modal
- **Role badge** on case list

Most of the existing UI works unchanged — just add an "Organization" column where relevant.

## Testing Strategy

- Integration tests for authorization: "user A cannot see user B's case"
- Integration tests for roles: "caseworker cannot invite members"
- Integration tests for cross-org isolation: "HateAid caseworker cannot see Weißer Ring's cases"
- Performance: 1000 cases per org, list endpoint returns in < 200ms

## Timeline (Sprint 1)

| Week | Deliverable |
|------|-------------|
| 1 (Apr 21-27) | Migration + new tables + auth dependency |
| 2 (Apr 28-May 4) | Org CRUD endpoints + member management |
| 3 (May 5-11) | Modify cases endpoints for org ownership + RLS |
| 4 (May 12-18) | UI: org switcher, org dashboard, member management |
| 5 (May 19-25) | Admin dashboard (metrics, case list across org) + bulk export |
| 6 (May 26-31) | Hardening, HateAid pitch prep |

## Open Questions

1. **Self-signup or invite-only?** Initial: invite-only (owner invites, email magic-link to accept). Prevents abuse at launch.
2. **Subscription / billing?** Initial: free for NGOs (Stiftung-funded). Post-launch: tiered (volunteer / professional / enterprise).
3. **White-labeling?** Org-level PDF letterhead yes; full white-label (remove SafeVoice branding) — post-MVP.
4. **Cross-org case transfer?** Sometimes HateAid refers to a specialist org. Deferred.
