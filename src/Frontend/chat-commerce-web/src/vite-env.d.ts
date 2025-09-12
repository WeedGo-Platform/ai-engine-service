/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_TENANT_ID: string
  readonly VITE_TENANT_CODE: string
  readonly VITE_TEMPLATE_ID: string
  readonly VITE_TEMPLATE: string
  readonly VITE_PORT: string
  readonly MODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare global {
  const __TENANT_CONFIG__: {
    tenantId: string;
    tenantCode: string;
    templateId: string;
  };
}

declare module '*.png' {
  const value: string;
  export default value;
}

declare module '*.jpg' {
  const value: string;
  export default value;
}

declare module '*.jpeg' {
  const value: string;
  export default value;
}

declare module '*.gif' {
  const value: string;
  export default value;
}

declare module '*.svg' {
  const value: string;
  export default value;
}

declare module '*.webp' {
  const value: string;
  export default value;
}