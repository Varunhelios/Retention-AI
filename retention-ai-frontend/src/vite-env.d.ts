/// <reference types="vite/client" />

// This helps TypeScript understand the @/ alias for imports
declare module "@/*" {
  const value: any;
  export default value;
}
