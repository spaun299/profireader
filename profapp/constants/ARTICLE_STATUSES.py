from profapp.models.rights import RIGHTS


# class ARTICLE_STATUS_IN_COMPANY:
#
#     EDITING = 'editing'
#     FINISHED = 'finished'
#     DELETED = 'deleted'
#     APPROVED = 'approved'
#
#     all = [editing, finished, accepted, declined]
#
#     @classmethod
#     def can_user_change_status_to(cls, from_status):
#         if from_status == cls.editing:
#             return [cls.accepted, cls.declined]
#
#         elif from_status == cls.accepted:
#             return [cls.declined]
#
#         elif from_status == cls.declined:
#             return [cls.accepted]
#
#         else:
#             return [cls.accepted, cls.declined]

class ARTICLE_STATUS_IN_PORTAL:

    editing = 'editing'
    finished = 'finished'
    accepted = 'deleted'
    declined = 'approved'

    published = 'published'
    not_published = 'not_published'
    declined = 'declined'
    all = [published, not_published, declined]

    @classmethod
    def can_user_change_status_to(cls, from_status):
        if from_status == cls.published:
            return [cls.not_published, cls.declined]

        elif from_status == cls.not_published:
            return [cls.published, cls.declined]

        elif from_status == cls.declined:
            return [cls.not_published, cls.published]

