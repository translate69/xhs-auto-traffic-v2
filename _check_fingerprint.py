import sys, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def check_fingerprint():
    with BrowserManager(headless=False) as (browser, context):
        page = context.new_page()
        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(3000)

        results = page.evaluate("""() => {
            return {
                // Automation
                webdriver: navigator.webdriver,
                chrome: typeof chrome !== 'undefined' ? chrome.runtime : null,

                // Canvas fingerprint
                canvas: (() => {
                    try {
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        canvas.width = 200; canvas.height = 50;
                        ctx.textBaseline = 'top';
                        ctx.font = '14px Arial';
                        ctx.fillStyle = '#f60';
                        ctx.fillRect(125, 1, 62, 20);
                        ctx.fillStyle = '#069';
                        ctx.fillText('Playwright fingerprint', 2, 15);
                        ctx.strokeStyle = 'rgba(102, 204, 0, 0.9)';
                        ctx.strokeText('Playwright fingerprint', 4, 17);
                        return canvas.toDataURL().slice(-50);
                    } catch(e) { return 'error: ' + e.message; }
                })(),

                // WebGL
                webgl: (() => {
                    try {
                        const canvas = document.createElement('canvas');
                        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                        if (!gl) return 'no webgl';
                        const ext = gl.getExtension('WEBGL_debug_renderer_info');
                        if (!ext) return 'no WEBGL_debug_renderer_info';
                        return gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
                    } catch(e) { return 'error: ' + e.message; }
                })(),

                // Navigator properties
                platform: navigator.platform,
                vendor: navigator.vendor,
                language: navigator.language,
                languages: JSON.stringify(navigator.languages),

                // Permissions
                permissions: JSON.stringify({
                    notifications: Notification.permission,
                    geolocation: (typeof geolocation !== 'undefined' ? 'defined' : 'undefined'),
                }),

                // Connection
                connection: JSON.stringify(navigator.connection || 'no navigator.connection'),

                // Hardware concurrency
                cpuClass: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,

                // Window
                outerWidth: window.outerWidth,
                outerHeight: window.outerHeight,
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
            };
        }""")

        print("=== Browser Fingerprint ===")
        for k, v in results.items():
            print(f"  {k}: {v}")

        page.close()

if __name__ == "__main__":
    check_fingerprint()
