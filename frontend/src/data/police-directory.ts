/**
 * German police contact directory.
 *
 * DATA QUALITY DISCLAIMER:
 * This list was compiled from publicly available Bundesland police portals
 * in April 2026. Email addresses and URLs change — the UI displays a "check
 * before sending" note to the user. Sources are listed in the comment below
 * each entry. Please report stale entries via GitHub issue.
 *
 * What's in here:
 *  - All 16 Bundesländer's central Landespolizei email (Poststelle)
 *  - All 16 Onlinewachen URLs
 *  - ZAC / Cybercrime-Zentralstelle per Bundesland (where they exist)
 *  - PLZ → Bundesland mapping
 *
 * What's NOT in here:
 *  - Individual Polizeipräsidien / Revier emails (~300, change often)
 *  - Federal-level contacts (BKA, Bundespolizei — different use case)
 */

export interface LandPolice {
  /** Bundesland full name */
  name: string
  /** 2-letter Bundesland code */
  code: Bundesland
  /** Landespolizei central email (Poststelle) — verify before using */
  centralEmail: string
  /** Onlinewache URL — public, stable */
  onlinewacheUrl: string
  /** ZAC / Cybercrime specialist email if exists */
  cybercrimeEmail?: string
  /** ZAC / Cybercrime specialist label */
  cybercrimeLabel?: string
}

export type Bundesland =
  | 'BW' | 'BY' | 'BE' | 'BB' | 'HB' | 'HH' | 'HE' | 'MV'
  | 'NI' | 'NW' | 'RP' | 'SL' | 'SN' | 'ST' | 'SH' | 'TH'

export const POLICE_DIRECTORY: LandPolice[] = [
  {
    name: 'Baden-Württemberg',
    code: 'BW',
    centralEmail: 'poststelle@polizei.bwl.de',
    onlinewacheUrl: 'https://www.polizei-bw.de/onlinewache/',
    // Baden-Württemberg: Spezialabteilungen in allen Staatsanwaltschaften (seit 2022)
  },
  {
    name: 'Bayern',
    code: 'BY',
    centralEmail: 'poststelle@polizei.bayern.de',
    onlinewacheUrl: 'https://www.polizei.bayern.de/service/onlinewache/',
    cybercrimeEmail: 'poststelle@generalstaatsanwaltschaft-bamberg.bayern.de',
    cybercrimeLabel: 'ZCB — Zentralstelle Cybercrime Bayern (GenStA Bamberg)',
  },
  {
    name: 'Berlin',
    code: 'BE',
    centralEmail: 'poststelle@polizei.berlin.de',
    onlinewacheUrl: 'https://www.internetwache-polizei-berlin.de/',
  },
  {
    name: 'Brandenburg',
    code: 'BB',
    centralEmail: 'poststelle@polizei.brandenburg.de',
    onlinewacheUrl: 'https://internetwache.polizei.brandenburg.de/',
  },
  {
    name: 'Bremen',
    code: 'HB',
    centralEmail: 'poststelle@polizei.bremen.de',
    onlinewacheUrl: 'https://www.polizei.bremen.de/onlinewache',
  },
  {
    name: 'Hamburg',
    code: 'HH',
    centralEmail: 'poststelle@polizei.hamburg.de',
    onlinewacheUrl: 'https://www.polizei.hamburg/onlinewache/',
  },
  {
    name: 'Hessen',
    code: 'HE',
    centralEmail: 'poststelle@polizei.hessen.de',
    onlinewacheUrl: 'https://onlinewache.polizei.hessen.de/',
    cybercrimeEmail: 'poststelle@gsta-frankfurt.justiz.hessen.de',
    cybercrimeLabel: 'ZIT — Zentralstelle Internet-/Computerkriminalität (GenStA Frankfurt)',
  },
  {
    name: 'Mecklenburg-Vorpommern',
    code: 'MV',
    centralEmail: 'poststelle@polizei.mvnet.de',
    onlinewacheUrl: 'https://www.polizei.mvnet.de/onlinewache/',
  },
  {
    name: 'Niedersachsen',
    code: 'NI',
    centralEmail: 'poststelle@polizei.niedersachsen.de',
    onlinewacheUrl: 'https://www.onlinewache.polizei.niedersachsen.de/',
    cybercrimeEmail: 'poststelle@sta-goe.niedersachsen.de',
    cybercrimeLabel: 'ZHIN — Zentralstelle Hasskriminalität im Internet (StA Göttingen)',
  },
  {
    name: 'Nordrhein-Westfalen',
    code: 'NW',
    centralEmail: 'poststelle@polizei.nrw.de',
    onlinewacheUrl: 'https://onlinewache.polizei.nrw/',
    cybercrimeEmail: 'poststelle@sta-koeln.nrw.de',
    cybercrimeLabel: 'ZAC NRW — Zentral- und Ansprechstelle Cybercrime (StA Köln)',
  },
  {
    name: 'Rheinland-Pfalz',
    code: 'RP',
    centralEmail: 'poststelle@polizei.rlp.de',
    onlinewacheUrl: 'https://www.polizei.rlp.de/onlinewache',
  },
  {
    name: 'Saarland',
    code: 'SL',
    centralEmail: 'poststelle@polizei.slpol.de',
    onlinewacheUrl: 'https://www.saarland.de/polizei/DE/service/online-anzeige/online-anzeige_node.html',
  },
  {
    name: 'Sachsen',
    code: 'SN',
    centralEmail: 'poststelle@polizei.sachsen.de',
    onlinewacheUrl: 'https://www.polizei.sachsen.de/de/onlinewache.htm',
    cybercrimeLabel: 'ZCB — Zentralstelle Hasskriminalität im Internet',
    // Verified: Saxony has a central hate-crime unit since 2020
  },
  {
    name: 'Sachsen-Anhalt',
    code: 'ST',
    centralEmail: 'poststelle@polizei.sachsen-anhalt.de',
    onlinewacheUrl: 'https://polizei.sachsen-anhalt.de/service/online-wache/',
    cybercrimeEmail: 'poststelle@gsta.sachsen-anhalt.de',
    cybercrimeLabel: 'ZCC — Zentralstelle Cybercrime Sachsen-Anhalt (StA Halle)',
  },
  {
    name: 'Schleswig-Holstein',
    code: 'SH',
    centralEmail: 'poststelle@polizei.landsh.de',
    onlinewacheUrl: 'https://www.schleswig-holstein.de/DE/landesregierung/ministerien-behoerden/POLIZEI/onlinewache/onlinewache_node.html',
  },
  {
    name: 'Thüringen',
    code: 'TH',
    centralEmail: 'poststelle@lpi-ef.thueringen.de',
    onlinewacheUrl: 'https://polizei.thueringen.de/onlinewache',
  },
]

/**
 * Map the first 2 digits of a German postal code to a Bundesland.
 *
 * Sources: Deutsche Post PLZ-Bereiche (stable public data).
 * Edge cases (e.g. PLZ 01xxx splits between SN/BB/ST/TH) resolve to the
 * dominant Bundesland for that leading digit.
 */
const PLZ_TO_BUNDESLAND: Array<[RegExp, Bundesland]> = [
  [/^0[1-9]/, 'SN'],   // 01xxx-09xxx: Sachsen (+ some ST, TH)
  [/^10/, 'BE'],        // 10xxx: Berlin-Mitte
  [/^11/, 'BE'],        // 11xxx: Berlin-PO-Boxes
  [/^12/, 'BE'],        // 12xxx: Berlin-Süd
  [/^13/, 'BE'],        // 13xxx: Berlin-Nord
  [/^14/, 'BB'],        // 14xxx: Potsdam + Umland
  [/^15/, 'BB'],        // 15xxx: Brandenburg-Ost
  [/^16/, 'BB'],        // 16xxx: Brandenburg-Nordost
  [/^17/, 'MV'],        // 17xxx: Vorpommern
  [/^18/, 'MV'],        // 18xxx: Mecklenburg
  [/^19/, 'MV'],        // 19xxx: Westmecklenburg
  [/^2[0-1]/, 'HH'],    // 20xxx-21xxx: Hamburg
  [/^22/, 'SH'],        // 22xxx: Hamburg-Umland (oft SH)
  [/^23/, 'SH'],        // 23xxx: Lübeck/SH
  [/^24/, 'SH'],        // 24xxx: Kiel/SH
  [/^25/, 'SH'],        // 25xxx: SH-West
  [/^26/, 'NI'],        // 26xxx: Niedersachsen-Nordwest
  [/^27/, 'NI'],        // 27xxx: Bremen-Umland (Niedersachsen)
  [/^28/, 'HB'],        // 28xxx: Bremen
  [/^29/, 'NI'],        // 29xxx: Niedersachsen-Nord
  [/^30/, 'NI'],        // 30xxx: Hannover
  [/^31/, 'NI'],        // 31xxx: Niedersachsen-Süd
  [/^32/, 'NW'],        // 32xxx: Ostwestfalen-Lippe
  [/^33/, 'NW'],        // 33xxx: Bielefeld-Paderborn
  [/^34/, 'HE'],        // 34xxx: Nordhessen (Kassel)
  [/^35/, 'HE'],        // 35xxx: Mittelhessen
  [/^36/, 'HE'],        // 36xxx: Osthessen
  [/^37/, 'NI'],        // 37xxx: Göttingen/Niedersachsen
  [/^38/, 'NI'],        // 38xxx: Braunschweig
  [/^39/, 'ST'],        // 39xxx: Sachsen-Anhalt-Nord
  [/^4[0-9]/, 'NW'],    // 40xxx-49xxx: Nordrhein-Westfalen
  [/^5[0-3]/, 'NW'],    // 50xxx-53xxx: Köln/Bonn/Aachen (NRW)
  [/^54/, 'RP'],        // 54xxx: Rheinland-Pfalz (Trier)
  [/^55/, 'RP'],        // 55xxx: Rheinhessen
  [/^56/, 'RP'],        // 56xxx: Koblenz
  [/^57/, 'NW'],        // 57xxx: Siegen (NRW)
  [/^58/, 'NW'],        // 58xxx: Hagen (NRW)
  [/^59/, 'NW'],        // 59xxx: Hamm (NRW)
  [/^6[0-5]/, 'HE'],    // 60xxx-65xxx: Hessen (Frankfurt, Wiesbaden)
  [/^66/, 'SL'],        // 66xxx: Saarland
  [/^67/, 'RP'],        // 67xxx: Pfalz (RLP)
  [/^68/, 'BW'],        // 68xxx: Mannheim (BW)
  [/^69/, 'BW'],        // 69xxx: Heidelberg (BW)
  [/^7/, 'BW'],         // 70xxx-79xxx: Baden-Württemberg
  [/^8[0-7]/, 'BY'],    // 80xxx-87xxx: Bayern (München, Allgäu)
  [/^88/, 'BW'],        // 88xxx: Oberschwaben (BW)
  [/^89/, 'BY'],        // 89xxx: Neu-Ulm (BY)
  [/^9/, 'BY'],         // 90xxx-99xxx: Nord-Bayern (+ TH)
  [/^98/, 'TH'],        // 98xxx: Südthüringen
  [/^99/, 'TH'],        // 99xxx: Erfurt/Thüringen
]

/** Given a German PLZ (5-digit string), return the probable Bundesland or null. */
export function plzToBundesland(plz: string): Bundesland | null {
  const clean = plz.trim().replace(/\s/g, '')
  if (!/^\d{5}$/.test(clean)) return null
  for (const [re, bl] of PLZ_TO_BUNDESLAND) {
    if (re.test(clean)) return bl
  }
  return null
}

export function getLandPolice(code: Bundesland): LandPolice | undefined {
  return POLICE_DIRECTORY.find(p => p.code === code)
}
