from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("connexion/", auth_views.LoginView.as_view(template_name="school/login.html"), name="login"),
    path("deconnexion/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("export/excel/", views.export_all_excel, name="export_all_excel"),
    path("classes/", views.class_list, name="class_list"),
    path("classes/ajouter/", views.class_create, name="class_create"),
    path("classes/<int:pk>/modifier/", views.class_update, name="class_update"),
    path("classes/<int:pk>/supprimer/", views.class_delete, name="class_delete"),
    path("frais-scolarite/", views.fee_list, name="fee_list"),
    path("frais-scolarite/ajouter/", views.fee_create, name="fee_create"),
        path("scolarite/", views.schooling_overview, name="schooling_overview"),
        path("scolarite/classes/<int:pk>/", views.schooling_class_detail, name="schooling_class_detail"),
        path("scolarite/eleves/<int:pk>/", views.student_payment_detail, name="student_payment_detail"),
        path("paiements/ajouter/", views.student_payment_create, name="student_payment_create"),
        path("paiements/<int:pk>/modifier/", views.student_payment_update, name="student_payment_update"),
        path("paiements/<int:pk>/supprimer/", views.student_payment_delete, name="student_payment_delete"),
    path("frais-scolarite/<int:pk>/modifier/", views.fee_update, name="fee_update"),
    path("frais-scolarite/<int:pk>/supprimer/", views.fee_delete, name="fee_delete"),
    path("eleves/", views.student_list, name="student_list"),
        path("eleves/<int:pk>/badge/", views.student_badge, name="student_badge"),
    path("eleves/inscrire/", views.student_create, name="student_create"),
    path("eleves/<int:pk>/modifier/", views.student_update, name="student_update"),
    path("eleves/<int:pk>/supprimer/", views.student_delete, name="student_delete"),
    path("utilisateurs/", views.user_list, name="user_list"),
    path("utilisateurs/creer/", views.user_create, name="user_create"),
    path("utilisateurs/<int:pk>/modifier/", views.user_update, name="user_update"),
    path("utilisateurs/<int:pk>/supprimer/", views.user_delete, name="user_delete"),
]