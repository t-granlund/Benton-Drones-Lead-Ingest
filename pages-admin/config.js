// Deploy-time configuration for the Pages admin dashboard.
// After the custom domain cutover, this is the branded API origin.
// For pre-cutover testing you may temporarily point at the Render default:
//   https://benton-drones-lead-ingest.onrender.com
// (remember CORS_ADMIN_ORIGIN on Render must match THIS site's origin)
window.ADMIN_API_BASE = "https://leads.bentondrones.com";
