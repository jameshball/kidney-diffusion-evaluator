from backend.index import app
from collections import defaultdict
from backend.model import *
from werkzeug.security import generate_password_hash
import statistics


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
            print(new_patch.id, new_patch.real, new_patch.version)
            db.session.add(new_patch)
        
        for patch in FAKE_PATCHES:
            patch_id, version = get_id_version(patch)
            patch_id = patch_id * 2 + 1
            if Patch.query.filter_by(id=patch_id).first():
                continue
            new_patch = Patch(id=patch_id, real=False, version=version)
            print(new_patch.id, new_patch.real, new_patch.version)
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


def calc_time_med(cs):
    times = [c.timestamp for c in cs]
    # how long it took the user to complete the later (j'th) classification
    time_diff = [((j-i).total_seconds(), idx) for (i, (idx, j)) in zip(times, enumerate(times[1:]))]
    # assume nobody will take longer than 5 mins per image
    time_diff = [(diff, idx) for (diff, idx) in time_diff if diff < 5 * 60]

    time_diff_correct = [diff for (diff, idx) in time_diff if cs[idx].classification]
    time_diff_incorrect = [diff for (diff, idx) in time_diff if not cs[idx].classification]
    time_diff = [diff for (diff, idx) in time_diff]

    correct_med = -1 if len(time_diff_correct) == 0 else statistics.median(time_diff_correct)
    incorrect_med = -1 if len(time_diff_incorrect) == 0 else statistics.median(time_diff_incorrect)
    med = -1 if len(time_diff) == 0 else statistics.median(time_diff)

    return med, correct_med, incorrect_med

def calc_classification_stats(classifications):
    classifications.sort(key=lambda x: x.timestamp)

    correct_classifications = [c for c in classifications if c.classification]
    incorrect_classifications = [c for c in classifications if not c.classification]

    num_correct = len(correct_classifications)
    num_incorrect = len(incorrect_classifications)

    total = num_correct + num_incorrect
    score = num_incorrect / total

    time_med, correct_time_med, incorrect_time_med = calc_time_med(classifications)

    return total, num_correct, num_incorrect, score, abs(score - 0.5), time_med, correct_time_med, incorrect_time_med


def show_classification_stats():
    TEST_USERS = ['jameshball', 'noor']

    with app.app_context():
        users = Member.query.all()
        all_users_versions = defaultdict(list)
        all_classifications = []
        all_error_versions = defaultdict(list)
        for user in users:
            print("statistics for", user.username)
            classifications = Classification.query.filter_by(user=user).all()
            if user.username not in TEST_USERS:
                all_classifications += classifications
            versions = defaultdict(list)

            for classification in classifications:
                version = classification.fake_patch.version
                version = 0 if version is None else version
                versions[version].append(classification)

            user_error = []
            for version in versions.keys():
                total, num_correct, num_incorrect, score, error, med_time, correct_med_time, incorrect_med_time = calc_classification_stats(versions[version])
                if user.username not in TEST_USERS:
                    all_users_versions[version] += versions[version]
                    all_error_versions[version].append((error, total))
                print("stats for version", version, ":")
                print(total, "images classified total:", num_correct, "correct, and", num_incorrect, "incorrect:", score, "absolute error:", error, "median time:", med_time, "median time when correct:", correct_med_time, "median time when incorrect:", incorrect_med_time)

            total, num_correct, num_incorrect, score, error, med_time, correct_med_time, incorrect_med_time = calc_classification_stats(classifications)
            print("overall stats")
            print(total, "images classified total:", num_correct, "correct, and", num_incorrect, "incorrect:", score, "median time:", med_time, "median time when correct:", correct_med_time, "median time when incorrect:", incorrect_med_time)
            print()

        print("-----------------------")
        print("overall statistics for all (production) users")
        print("-----------------------")
        for version in all_users_versions.keys():
            total, num_correct, num_incorrect, score, error, med_time, correct_med_time, incorrect_med_time = calc_classification_stats(all_users_versions[version])
            weighted_abs = [num_classified * abs_error / total for abs_error, num_classified in all_error_versions[version]]
            version_mae = sum(weighted_abs)
            print("stats for version", version, ":")
            print(total, "images classified total:", num_correct, "correct, and", num_incorrect, "incorrect:", score, "MEAN WEIGHTED ABS ERROR:", version_mae, "median time:", med_time, "median time when correct:", correct_med_time, "median time when incorrect:", incorrect_med_time)

        total, num_correct, num_incorrect, score, error, med_time, correct_med_time, incorrect_med_time = calc_classification_stats(all_classifications)
        print("overall stats")
        print(total, "images classified total:", num_correct, "correct, and", num_incorrect, "incorrect:", score, "median time:", med_time, "median time when correct:", correct_med_time, "median time when incorrect:", incorrect_med_time)
        print()




def clear_classifications(username):
    with app.app_context():
        user = Member.query.filter_by(username=username).first()
        if not user:
            print('User does not exist')
            return

        Classification.query.filter_by(user=user).delete()
        db.session.commit()


if __name__ == '__main__':
    pass
