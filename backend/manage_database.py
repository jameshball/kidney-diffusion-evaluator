from backend.index import app
from backend.model import *
from werkzeug.security import generate_password_hash


def delete_all():
    with app.app_context():
        Classification.query.delete()
        Patch.query.delete()
        Member.query.delete()
        db.session.commit()


def create_db():
    with app.app_context():
        db.create_all()


def delete_user(username):
    with app.app_context():
        user = Member.query.filter_by(username=username).first()
        if user:
            Classification.query.filter_by(user=user).delete()
            db.session.delete(user)
            db.session.commit()


def add_user(username, password, hash=True):
    with app.app_context():
        user = Member.query.filter_by(username=username).first() # if this returns a user, then the email already exists in database

        if user:
            print('User already exists')
            return

        password = generate_password_hash(password, method='sha256') if hash else password
        new_user = Member(username=username, password=password)

        db.session.add(new_user)
        db.session.commit()


def get_id_version(filename):
    filename = filename.split('.')[0]
    id_version = filename.split('_')
    if len(id_version) == 2:
        patch_id = int(id_version[0])
        version = int(id_version[1])
    else:
        patch_id = int(id_version[0])
        version = 0
    
    return patch_id, version


def initialise_patches(force=False):
    with app.app_context():
        if force:
            Patch.query.delete()
            db.session.commit()

        for patch in REAL_PATCHES:
            # get id from filename without extension
            patch_id, version = get_id_version(patch)
            patch_id = patch_id * 2
            # check if patch already exists
            if Patch.query.filter_by(id=patch_id).first():
                continue
            # add patch to database
            new_patch = Patch(id=patch_id, real=True, version=version)
            print(new_patch)
            db.session.add(new_patch)
        
        for patch in FAKE_PATCHES:
            patch_id, version = get_id_version(patch)
            patch_id = patch_id * 2 + 1
            if Patch.query.filter_by(id=patch_id).first():
                continue
            new_patch = Patch(id=patch_id, real=False, version=version)
            print(new_patch)
            db.session.add(new_patch)
        
        db.session.commit()


def list_classifications(username):
    with app.app_context():
        user = Member.query.filter_by(username=username).first()
        if not user:
            print('User does not exist')
            return

        classifications = Classification.query.filter_by(user=user).all()
        for classification in classifications:
            print(classification.classification, classification.timestamp, "real patch id:", classification.real_patch_id, "fake patch id:", classification.fake_patch_id, "fake patch version:", classification.fake_patch.version)


def clear_classifications(username):
    with app.app_context():
        user = Member.query.filter_by(username=username).first()
        if not user:
            print('User does not exist')
            return

        Classification.query.filter_by(user=user).delete()
        db.session.commit()


if __name__ == '__main__':
    create_db()
    add_user('jameshball', 'sha256$cGLO0lBcmvOdxGIx$a9cc6c4da79f99b41216ffc99a6d4257c2910ca2fc5a0f6f69c05c1fef4725c9', hash=False)
    initialise_patches(force=True)
    pass
