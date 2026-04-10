import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _get_defaultdeptid(section_nom):
    """
    Trouve le deptid dans la table departments (Attendance Management)
    en matchant le nom de section avec deptname.
    """
    from presence.models import Departments

    if section_nom:
        dept = Departments.objects.filter(
            deptname__iexact=section_nom
        ).first()
        if dept:
            return dept.deptid

    # Fallback : ADMINISTRATION
    dept_default = Departments.objects.filter(
        deptname__iexact='ADMINISTRATION'
    ).first()
    return dept_default.deptid if dept_default else 1


@receiver(post_save, sender='personnel.InformationPersonnelle')
def sync_userinfo_on_save(sender, instance, created, **kwargs):
    from presence.models import UserInfo

    if created:
        max_userid = UserInfo.objects.order_by('-userid').first()
        next_userid = (max_userid.userid + 1) if max_userid else 1

        UserInfo.objects.create(
            userid=next_userid,
            badgenumber=instance.numero_matricule,
            ssn=instance.CIN or '',
            name=instance.nom_complet,
            defaultdeptid=None,
        )
    else:
        UserInfo.objects.filter(
            badgenumber=instance.numero_matricule
        ).update(
            ssn=instance.CIN or '',
            name=instance.nom_complet,
        )


@receiver(post_save, sender='personnel.InformationProfessionnelle')
def sync_userinfo_on_infopro_save(sender, instance, created, **kwargs):
    """
    Quand InformationProfessionnelle est créée/modifiée →
    mettre à jour defaultdeptid (depuis departments) et UserSection.
    """
    from presence.models import UserInfo, UserSection, Section
    from presence.utils import _effective_section

    try:
        employe = instance.employe
        section_nom = _effective_section(instance.section, instance.responsable_section)

        if not section_nom:
            return

        # ── 1. deptid depuis departments (Attendance Management) ─────────
        deptid = _get_defaultdeptid(section_nom)
        logger.info(f"Section: {section_nom} → deptid: {deptid}")

        # ── 2. section_obj depuis db_section (Django) ────────────────────
        section_obj = Section.objects.filter(
            nom_section__iexact=section_nom
        ).first()
        if not section_obj:
            section_obj = Section.objects.create(nom_section=section_nom)

        # ── 3. Mettre à jour UserInfo.defaultdeptid ──────────────────────
        user = UserInfo.objects.filter(
            badgenumber=employe.numero_matricule
        ).first()

        if user:
            UserInfo.objects.filter(
                badgenumber=employe.numero_matricule
            ).update(defaultdeptid=deptid)  # ← deptid de departments ✅

            # ── 4. Mettre à jour UserSection ─────────────────────────────
            UserSection.objects.update_or_create(
                userid=user.userid,
                defaults={'section': section_obj}
            )

    except Exception as e:
        logger.error(f"Erreur sync_userinfo_on_infopro_save: {e}")


@receiver(post_delete, sender='personnel.InformationPersonnelle')
def sync_userinfo_on_delete(sender, instance, **kwargs):
    from presence.models import UserInfo

    UserInfo.objects.filter(
        badgenumber=instance.numero_matricule
    ).delete()