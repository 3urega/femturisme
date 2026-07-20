"""Admin HTML UI for guide documents (plan §9, issue #32)."""
from __future__ import annotations

from flask import Blueprint, render_template

admin_ui_bp = Blueprint('admin_ui', __name__)


@admin_ui_bp.route('/guides')
def guides_list():
    return render_template('admin/guides_list.html')


@admin_ui_bp.route('/guides/upload')
def guides_upload():
    return render_template('admin/guides_upload.html')


@admin_ui_bp.route('/guides/<uuid:doc_id>')
def guides_detail(doc_id):
    return render_template('admin/guides_detail.html', doc_id=str(doc_id))
