import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 5173 is usually taken on this machine by another course project, so the desk
// gets its own port. The backend's CORS allows any localhost port.
export default defineConfig({
  plugins: [react()],
  server: { port: 5181, strictPort: false, open: false },
});
