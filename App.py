import atexit
import signal

from flask import Flask
from models.RepositoryStructureAnalyzer import RepositoryStructureAnalyzer

app = Flask(__name__, template_folder='views/templates', static_folder='views/static')

_cleanup_done = False


def _cleanup_cloned_repositories():
    """Elimina solo repositorios temporales usados en esta sesion de servidor."""
    global _cleanup_done
    if _cleanup_done:
        return

    cleanup_summary = RepositoryStructureAnalyzer.cleanup_tracked_repositories()
    removed_count = len(cleanup_summary.get("removed", []))
    not_found_count = len(cleanup_summary.get("not_found", []))
    failed_entries = cleanup_summary.get("failed", [])

    print(
        "[CLEANUP] Repositorios temporales (sesion actual) | "
        f"eliminados={removed_count}, no_encontrados={not_found_count}, fallidos={len(failed_entries)}"
    )
    for failure in failed_entries[:5]:
        print(f"[CLEANUP] Fallo en {failure['path']}: {failure['error']}")
    if len(failed_entries) > 5:
        print("[CLEANUP] ...")

    _cleanup_done = True


def _handle_shutdown_signal(signum, _frame):
    """Asegura limpieza al detener la app con Ctrl+C o terminacion del proceso."""
    _cleanup_cloned_repositories()
    raise SystemExit(0)


# Limpieza al finalizar el proceso por salida normal.
atexit.register(_cleanup_cloned_repositories)

# Limpieza al recibir senales de cierre.
signal.signal(signal.SIGINT, _handle_shutdown_signal)
signal.signal(signal.SIGTERM, _handle_shutdown_signal)

from controllers.main_controller import main_bp
app.register_blueprint(main_bp)

if __name__ == "__main__":
    app.run(debug=True)