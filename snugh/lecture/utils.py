from lecture.models import Semester, SemesterLecture, Plan
from snugh.snugh.exceptions import NotFound
from user.models import Major, User
from lecture.const import *
from django.db.models import Case, When, Value, IntegerField
from snugh.exceptions import NotOwner

# Common Functions
def add_credits(semesterlecture):
    semester = semesterlecture.semester
    if semesterlecture.lecture_type == MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type2 == MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == MAJOR_ELECTIVE or semesterlecture.lecture_type == TEACHING:
        semester.major_elective_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL:
        semester.general_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.credit
    return semester


def subtract_credits(semesterlecture):
    semester = semesterlecture.semester
    if semesterlecture.lecture_type == MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type2 == MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == MAJOR_ELECTIVE or semesterlecture.lecture_type == TEACHING:
        semester.major_elective_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL:
        semester.general_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL_ELECTIVE:
        semester.general_elective_credit -= semesterlecture.credit
    return semester


def add_semester_credits(semesterlecture: SemesterLecture, semester: Semester) -> Semester:
    """ Add SemesterLecture's credits to Semester credits. """
    if semesterlecture.lecture_type == MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type2 == MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == MAJOR_ELECTIVE or semesterlecture.lecture_type == TEACHING:
        semester.major_elective_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL:
        semester.general_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.credit
    return semester

def sub_semester_credits(semesterlecture: SemesterLecture, semester: Semester) -> Semester:
    """ Subtract SemesterLecture's credits to Semester credits. """
    if semesterlecture.lecture_type == MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type2 == MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == MAJOR_ELECTIVE or semesterlecture.lecture_type == TEACHING:
        semester.major_elective_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL:
        semester.general_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL_ELECTIVE:
        semester.general_elective_credit -= semesterlecture.credit
    return semester

def update_lecture_info(\
    user: User, 
    plan_id: int, 
    semesterlectures: SemesterLecture = None, 
    semester: Semester = None) -> Plan:
    """ Update lecture info """
    try:
        plan = Plan.objects.prefetch_related(
                'user',
                'user__userprofile',
                'semester', 
                'planmajor',
                'semester__semesterlecture',
                'semester__semesterlecture__lecture',
                'semester__semesterlecture__lecture__majorlecture',
                'semester__semesterlecture__lecture__lecturecredit'
                ).get(id=plan_id)
    except Plan.DoesNotExist:
        raise NotFound()
    owner = plan.user
    if user != owner:
        raise NotOwner()
    planmajors = plan.planmajor.all()
    #TODO: Major 없애기
    majors = Major.objects.filter(planmajor__in=planmajors)\
        .annotate(custom_order=Case(When(major_type=Major.SINGLE_MAJOR, then=Value(0)),
                                    When(major_type=Major.MAJOR, then=Value(1)),
                                    When(major_type=Major.GRADUATE_MAJOR, then=Value(2)),
                                    When(major_type=Major.INTERDISCIPLINARY_MAJOR, then=Value(3)),
                                    When(major_type=Major.INTERDISCIPLINARY_MAJOR_FOR_TEACHER, then=Value(4)),
                                    When(major_type=Major.DOUBLE_MAJOR, then=Value(5)),
                                    When(major_type=Major.INTERDISCIPLINARY, then=Value(6)),
                                    When(major_type=Major.MINOR, then=Value(7)),
                                    When(major_type=Major.INTERDISCIPLINARY_PROGRAM, then=Value(8)),
                                    default=Value(9),
                                    output_field=IntegerField(), ))\
        .order_by('custom_order')
    none_major = Major.objects.get(id=DEFAULT_MAJOR_ID)
    updated_semesters = []
    if semesterlectures and semester:
        updated_semester = __update_lecture_info(user, majors, semesterlectures, semester, none_major)
        updated_semesters.append(updated_semester)
    else:
        semesters = plan.semester.all()
        for semester in semesters:
            semesterlectures = semester.semesterlecture.all()
            updated_semester = __update_lecture_info(user, majors, semesterlectures, semester, none_major)
            updated_semesters.append(updated_semester)
    Semester.objects.bulk_update(
        updated_semesters, 
        ['major_requirement_credit', 
        'major_elective_credit', 
        'general_credit', 
        'general_elective_credit'])
    return plan

def __update_lecture_info(
    user:User, 
    majors: Major, 
    semesterlectures: SemesterLecture, 
    semester: Semester,
    none_major: Major = Major.objects.get(id=DEFAULT_MAJOR_ID)) -> Semester:

    updated_semesterlectures = []
    for semesterlecture in semesterlectures:
        tmp_majors = majors

        if not semesterlecture.is_modified:
            semester = sub_semester_credits(semesterlecture, semester)
            lecture = semesterlecture.lecture

            if semesterlecture.lecture_type != GENERAL:
                major_count = 0
                std = user.userprofile.entrance_year
                majorlectures = lecture.majorlecture.all()
                for major in tmp_majors:
                    if major_count > 1:
                        break
                    candidate_majorlectures = majorlectures.filter(
                        major=major,
                        start_year__lte=std,
                        end_year__gte=std)\
                    .exclude(lecture_type__in=[GENERAL, GENERAL_ELECTIVE])\
                    .order_by('-lecture_type')

                    if candidate_majorlectures.exists():
                        candidate_majorlecture = candidate_majorlectures[0]
                        if major_count == 0:
                            semesterlecture.lecture_type = candidate_majorlecture.lecture_type
                            semesterlecture.lecture_type1 = candidate_majorlecture.lecture_type
                            semesterlecture.recognized_major1 = major
                        elif major_count == 1:
                            semesterlecture.lecture_type2 = candidate_majorlecture.lecture_type
                            semesterlecture.recognized_major2 = major
                        major_count += 1

                if major_count != 2:
                    if major_count == 1:
                        tmp_majors = tmp_majors.exclude(id=major.id)
                    std = semester.year

                    for major in tmp_majors:
                        if major_count > 1:
                            break

                        candidate_majorlectures = lecture.majorlecture.filter(
                            major=major,
                            start_year__lte=std,
                            end_year__gte=std)\
                        .exclude(lecture_type__in=[GENERAL, GENERAL_ELECTIVE])\
                        .order_by('-lecture_type')

                        if candidate_majorlectures.exists() != 0:
                            candidate_majorlecture = candidate_majorlectures[0]
                            if major_count == 0:
                                semesterlecture.lecture_type = candidate_majorlecture.lecture_type
                                semesterlecture.lecture_type1 = candidate_majorlecture.lecture_type
                                semesterlecture.recognized_major1 = major
                            elif major_count == 1:
                                semesterlecture.lecture_type2 = candidate_majorlecture.lecture_type
                                semesterlecture.recognized_major2 = major
                            major_count += 1

                if major_count == 1:
                    semesterlecture.lecture_type2 = NONE
                    semesterlecture.recognized_major2 = none_major
                elif major_count == 0:
                    semesterlecture.lecture_type = GENERAL_ELECTIVE
                    semesterlecture.lecture_type1 = GENERAL_ELECTIVE
                    semesterlecture.recognized_major1 = none_major
                    semesterlecture.lecture_type2 = NONE
                    semesterlecture.recognized_major2 = none_major

            lecturecredits = lecture.lecturecredit.filter(start_year__lte=semester.year,
                                                            end_year__gte=semester.year)

            if lecturecredits.exists():
                semesterlecture.credit = lecturecredits[0].credit

            semester = add_semester_credits(semesterlecture, semester)
            updated_semesterlectures.append(semesterlecture)
    SemesterLecture.objects.bulk_update(
        updated_semesterlectures, 
        ['lecture_type', 
        'lecture_type1', 
        'recognized_major1', 
        'lecture_type2', 
        'recognized_major2', 
        'credit'])
    return semester
