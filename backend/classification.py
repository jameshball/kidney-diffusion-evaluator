from datetime import datetime
import os

from flask import Blueprint, request, jsonify, send_file
from flask_login import current_user, login_required
from sqlalchemy.sql.expression import func

from backend.model import db, Classification, Patch, Member, PATCH_DIR

classification = Blueprint('classification', __name__)


def get_classification():
    u = current_user
    
    # get a real patch and a fake patch that the user hasn't classified with the
    # smallest id
    real_patch = (
        db.session.query(Patch)
        .filter_by(real=True)
        .filter(~Patch.real_classifications.any(Classification.user_id == u.id))
        .order_by(Patch.id)
        .first()
    )
    fake_patch = (
        db.session.query(Patch)
        .filter_by(real=False)
        .filter(~Patch.fake_classifications.any(Classification.user_id == u.id))
        .order_by(Patch.id)
        .first()
    )

    # get the number of unique classifications the user has made
    num_classifications = (
        db.session.query(Classification)
        .filter_by(user=u)
        .group_by(Classification.real_patch_id, Classification.fake_patch_id)
        .count()
    )

    if not real_patch or not fake_patch:
        return None, None, num_classifications
    
    return real_patch, fake_patch, num_classifications


@classification.route('/classification', methods=['POST'])
@login_required
def post_classification():
    u = current_user
    real_patch_id = request.form.get('real_patch_id')
    fake_patch_id = request.form.get('fake_patch_id')
    classification = request.form.get('classification')

    if not real_patch_id or not fake_patch_id or not classification:
        return jsonify(
            success=False,
            message='Missing data',
        )

    real_patch = Patch.query.filter_by(id=real_patch_id).first()
    fake_patch = Patch.query.filter_by(id=fake_patch_id).first()

    if not real_patch or not fake_patch:
        return jsonify(
            success=False,
            message='Invalid patch IDs',
        )
    
    print(real_patch_id, fake_patch_id, classification)

    new_classification = Classification(
        real_patch=real_patch,
        fake_patch=fake_patch,
        user=u,
        classification=classification == 'real',
    )
    db.session.add(new_classification)
    db.session.commit()

    return jsonify(
        success=True,
    )


@classification.route('/patch', methods=['GET'])
@login_required
def get_patch():
    patch_id = request.args.get('id', type=int)

    if not patch_id:
        return jsonify(
            success=False,
            message='Missing data',
        )
    
    patch = Patch.query.filter_by(id=patch_id).first()

    if not patch:
        return jsonify(
            success=False,
            message='Invalid patch ID',
        )
    
    if patch.real:
        patch_id = patch_id // 2
        path = os.path.join(PATCH_DIR, 'real', f'{patch_id}.png')
    else:
        patch_id = (patch_id - 1) // 2
        path = os.path.join(PATCH_DIR, 'fake', f'{patch_id}.png')
    
    return send_file(path)

    