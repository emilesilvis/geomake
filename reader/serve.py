"""Preview the same /geomake/ and /static/css/ paths used by the existing site."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--site-css", type=Path, default=ROOT / "host-style.css")
    args = parser.parse_args()
    if not (ROOT / "dist/index.html").is_file():
        parser.error("Run python3 reader/build.py first.")
    with tempfile.TemporaryDirectory(prefix="geomake-preview-") as temporary:
        preview = Path(temporary)
        (preview / "geomake").symlink_to(ROOT / "dist", target_is_directory=True)
        (preview / "static/css").mkdir(parents=True)
        (preview / "static/css/style.css").symlink_to(args.site_css.resolve())
        server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(SimpleHTTPRequestHandler, directory=preview))
        print(f"http://localhost:{server.server_port}/geomake/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
