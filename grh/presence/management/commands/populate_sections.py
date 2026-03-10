# presence/management/commands/populate_sections.py
"""
Peuple db_section et db_user_section à partir de InformationProfessionnelle.

Règle :
  section_effective = responsable_section  si non vide
                    = section              sinon
"""

from django.core.management.base import BaseCommand

from presence.models import Section, UserSection, UserInfo
from personnel.models import InformationPersonnelle, InformationProfessionnelle


class Command(BaseCommand):
    help = "Peuple db_section et db_user_section depuis InformationProfessionnelle"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Affiche les résultats sans toucher à la base"
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        self.stdout.write("═" * 60)
        self.stdout.write("  PEUPLEMENT db_section + db_user_section")
        self.stdout.write("═" * 60)

        # ── 1. Collecter les sections effectives depuis InformationProfessionnelle ──
        qs = InformationProfessionnelle.objects.select_related('employe').all()

        sections_set: set[str] = set()
        employe_section_map: dict[int, str] = {}   # employe.pk → section_effective

        for ip in qs:
            raw = ip.responsable_section.strip() if ip.responsable_section else ""
            if not raw:
                raw = ip.section.strip() if ip.section else ""
            if raw:
                nom = raw.upper()
                sections_set.add(nom)
                employe_section_map[ip.employe_id] = nom

        self.stdout.write(f"\n[1] Sections uniques trouvées : {len(sections_set)}")
        for s in sorted(sections_set):
            self.stdout.write(f"    • {s}")

        if dry_run:
            self.stdout.write("\n[DRY-RUN] Aucune modification effectuée.")
            return

        # ── 2. Créer / récupérer les objets Section ──
        created_sections = 0
        section_objs: dict[str, Section] = {}
        for nom in sections_set:
            obj, created = Section.objects.get_or_create(nom_section=nom)
            section_objs[nom] = obj
            if created:
                created_sections += 1

        self.stdout.write(f"\n[2] Sections créées en base : {created_sections}")

        # ── 3. Mettre à jour section_ref dans InformationProfessionnelle ──
        updated_infopro = 0
        for ip in qs:
            nom = employe_section_map.get(ip.employe_id)
            if nom:
                section_obj = section_objs.get(nom)
                if ip.section_ref_id != (section_obj.pk if section_obj else None):
                    ip.section_ref = section_obj
                    # Contourner le verrou sur les champs sensibles
                    InformationProfessionnelle.objects.filter(pk=ip.pk).update(
                        section_ref=section_obj
                    )
                    updated_infopro += 1

        self.stdout.write(f"[3] InformationProfessionnelle.section_ref mis à jour : {updated_infopro}")

        # ── 4. Créer / mettre à jour UserSection ──
        # Construire un dict badgenumber → section_nom
        badge_section: dict[str, str] = {}
        for ip in qs:
            nom = employe_section_map.get(ip.employe_id)
            if nom:
                badge = ip.employe.numero_matricule
                badge_section[badge] = nom

       # ── 4. Créer / mettre à jour UserSection ──
        created_us = updated_us = skipped_us = 0
        for user in UserInfo.objects.all():
            nom = badge_section.get(user.badgenumber)
            if not nom:
                skipped_us += 1
                continue
            section_obj = section_objs.get(nom)
            if not section_obj:
                skipped_us += 1
                continue
            _, created = UserSection.objects.update_or_create(
                userid=user.userid,                      # ← userid au lieu de user=user
                defaults={'section': section_obj},
            )
            if created:
                created_us += 1
            else:
                updated_us += 1

        self.stdout.write(f"[4] UserSection — créés: {created_us}, mis à jour: {updated_us}, ignorés: {skipped_us}")
        self.stdout.write("\n✅  Terminé avec succès.")
