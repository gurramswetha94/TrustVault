"""
TrustVault Search Routes
Implements multi-parameter search (name, owner, category, date range)
strictly bounded by caller authorization to prevent metadata leakage.
"""

from datetime import datetime
from flask import Blueprint, render_template, request
from models import Document, User
from services.auth_service import login_required, get_current_user
from services.permission_service import get_accessible_documents_query

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
@login_required
def search():
    user = get_current_user()
    
    query_text = request.args.get('q', '').strip()
    owner_query = request.args.get('owner', '').strip()
    category_filter = request.args.get('category', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    
    # Fundamental Security Wall: Base query contains ONLY accessible documents
    query = get_accessible_documents_query(user)
    
    # 1. Filter by keyword (Name / Title / Description)
    if query_text:
        query = query.filter(
            (Document.title.ilike(f"%{query_text}%")) |
            (Document.description.ilike(f"%{query_text}%")) |
            (Document.original_filename.ilike(f"%{query_text}%"))
        )
        
    # 2. Filter by Owner username
    if owner_query:
        query = query.join(User, Document.owner_id == User.id).filter(
            User.username.ilike(f"%{owner_query}%")
        )
        
    # 3. Filter by Category
    if category_filter:
        query = query.filter(Document.category == category_filter)
        
    # 4. Filter by Date range
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Document.created_at >= dt_from)
        except ValueError:
            pass
            
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            # Include entire end day
            dt_to = dt_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Document.created_at <= dt_to)
        except ValueError:
            pass
            
    results = query.order_by(Document.created_at.desc()).all()
    
    return render_template(
        'search_results.html',
        user=user,
        results=results,
        query_text=query_text,
        owner_query=owner_query,
        category_filter=category_filter,
        date_from=date_from,
        date_to=date_to,
        total_count=len(results)
    )

