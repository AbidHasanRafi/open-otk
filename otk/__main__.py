"""
Command-line entry point for OTK GUI.
Allows running: python -m otk
Supports: python -m otk --version
"""

import sys
import os

def main():
    """Launch the OTK GUI with CLI argument support"""
    
    # Handle --version and --help FIRST before doing anything else
    if '--version' in sys.argv or '-v' in sys.argv:
        print('Open OTK v1.0.7')
        print('Author: Md. Abid Hasan Rafi')
        print('Powered by AI Extension')
        print('License: MIT')
        sys.exit(0)
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print('usage: python -m otk [-h] [--version]')
        print('')
        print('Open OTK - Professional Ollama Toolkit')
        print('')
        print('options:')
        print('  -h, --help     show this help message and exit')
        print('  --version, -v  show program version number and exit')
        print('')
        print('Examples:')
        print('  python -m otk              Launch GUI')
        print('  python -m otk --version    Show version information')
        print('  python -m otk --help       Show this help message')
        print('')
        print('Shortcut (if in PATH):')
        print('  otk                        Launch GUI')
        print('  otk --version              Show version')
        print('')
        print('For library usage:')
        print('  from otk import OllamaClient, ChatSession, ModelManager')
        sys.exit(0)
    
    # Now launch the GUI
    try:
        # Look for the GUI launcher in site-packages
        import importlib.util
        import site
        
        # Search in site-packages for the standalone otk.py module
        found = False
        for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
            if site_dir is None:
                continue
            otk_path = os.path.join(site_dir, 'otk.py')
            if os.path.exists(otk_path):
                spec = importlib.util.spec_from_file_location("otk_launcher", otk_path)
                if spec and spec.loader:
                    otk_launcher = importlib.util.module_from_spec(spec)
                    sys.modules['otk_launcher'] = otk_launcher
                    
                    # Remove --version/--help from sys.argv so GUI doesn't see them
                    original_argv = sys.argv[:]
                    sys.argv = [sys.argv[0]]  # Keep only script name
                    
                    try:
                        spec.loader.exec_module(otk_launcher)
                        if hasattr(otk_launcher, 'main'):
                            otk_launcher.main()
                            found = True
                    finally:
                        sys.argv = original_argv
                    break
        
        if not found:
            print("⚠️  OTK GUI Launcher")
            print("\\nCouldn't find the OTK GUI module.")
            print("\\n✅ Try these alternatives:")
            print('  python -c "import otk; otk.main()"')
            print("\\n📝 Or add Python Scripts to PATH and use:")
            print("  otk")
            print("\\n🔧 Installation issue? Reinstall:")
            print("  pip install --force-reinstall open-otk")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\\n\\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error launching OTK: {e}")
        print("\\n🔧 Troubleshooting:")
        print("  pip install --force-reinstall open-otk")
        print("\\n📖 Documentation:")
        print("  https://github.com/aiextension/open-otk")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
