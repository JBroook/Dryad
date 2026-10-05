from django.core.management.base import BaseCommand

from projects.models import Project


class Command(BaseCommand):
    help = 'Delete all Project records named "Penang Taman Negara".'

    def handle(self, *args, **options):
        queryset = Project.objects.filter(name='Penang Taman Negara')
        count = queryset.count()

        if count == 0:
            self.stdout.write(
                self.style.WARNING('No Project records named "Penang Taman Negara" were found.')
            )
            return

        queryset.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {count} Project record(s) named "Penang Taman Negara".'
            )
        )
