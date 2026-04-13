/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_OPERATOR_NAME?: string
  readonly VITE_OPERATOR_STREET?: string
  readonly VITE_OPERATOR_CITY?: string
  readonly VITE_OPERATOR_COUNTRY?: string
  readonly VITE_OPERATOR_EMAIL?: string
  readonly VITE_OPERATOR_PHONE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
