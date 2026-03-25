import sys
import os

# Add the src directory to sys.path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

print('Backend directory:', backend_dir)
print('Source directory:', src_dir)
print('Python path[0]:', sys.path[0])

# Check if the main.py file exists
main_file = os.path.join(src_dir, 'review_clustering', 'main.py')
print('Main.py exists:', os.path.exists(main_file))

# Test basic imports
try:
    print('Testing basic imports...')
    import flask
    print('✅ Flask imported')
except ImportError as e:
    print('❌ Flask import failed:', e)

try:
    print('Testing flask_cors...')
    from flask_cors import CORS
    print('✅ flask_cors imported')
except ImportError as e:
    print('❌ flask_cors import failed:', e)

# Test the main import
try:
    print('Testing main import...')
    from review_clustering.main import app
    print('✅ Main import successful!')
    print('App:', app)
except ImportError as e:
    print('❌ Main import failed:', e)
    print('Error details:', str(e))
    
    # Try to debug further
    try:
        import review_clustering
        print('✅ review_clustering package imported')
        print('Package location:', review_clustering.__file__)
    except ImportError as e2:
        print('❌ review_clustering package import failed:', e2)
