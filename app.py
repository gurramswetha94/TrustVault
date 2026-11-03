"""
TrustVault Main Application Factory
Wires together configuration, database, security middleware, and blueprints.
"""

import os
from flask import Flask, render_template
from config import Config
from models import db
from services.auth_service import get_current_user

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Ensure storage directory exists
    os.makedirs(app.config['VAULT_STORAGE_DIR'], exist_ok=True)
    
    # Context processor to inject current_user and system metadata into all templates
    @app.context_processor
    def inject_global_template_vars():
        return {
            'current_user': get_current_user(),
            'app_name': 'TrustVault'
        }
        
    # Register Route Blueprints
    from routes.auth_routes import auth_bp
    from routes.document_routes import document_bp
    from routes.permission_routes import permission_bp
    from routes.search_routes import search_bp
    from routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(permission_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(admin_bp)
    
    # Custom Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('error.html', 
                               error_code=403, 
                               error_title="Access Forbidden", 
                               error_description=str(error.description if hasattr(error, 'description') else "You do not have permission to access this resource.")), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', 
                               error_code=404, 
                               error_title="Resource Not Found", 
                               error_description="The requested document or endpoint was not found."), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template('error.html', 
                               error_code=413, 
                               error_title="Upload Ceiling Exceeded", 
                               error_description="File exceeds the maximum allowable size ceiling of 25 MB."), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html', 
                               error_code=500, 
                               error_title="Internal Server Error", 
                               error_description="An unexpected server error occurred. This event has been logged."), 500

    # Auto-initialize tables within app context
    with app.app_context():
        db.create_all()
        
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

