from __future__ import annotations

from django.contrib import admin

from .models import User

class UserAdmin(admin.ModelAdmin):
    # Champs à afficher dans la liste
    list_display = ('username', 'email', 'role', 'email_confirmed', 'is_active', 'is_staff')

    # Champs de recherche
    search_fields = ('username', 'email')

    # Méthodes pour contrôler les permissions (ajout, modification, suppression)
    def has_add_permission(self, request):
        return True  # Autoriser l'ajout d'utilisateurs via l'admin

    def has_change_permission(self, request, obj=None):
        return True  # Autoriser la modification des utilisateurs via l'admin

    def has_delete_permission(self, request, obj=None):
        return True  # Autoriser la suppression des utilisateurs via l'admin

# Enregistrement du modèle User avec votre configuration personnalisée
admin.site.register(User, UserAdmin)
