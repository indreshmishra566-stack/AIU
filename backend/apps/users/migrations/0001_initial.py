"""
AIU — Users: Initial Migration
Creates: users, user_profiles, user_devices tables.
"""

import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import encrypted_model_fields.fields
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True, verbose_name="email address")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("role", models.CharField(choices=[("user","User"),("premium","Premium"),("admin","Admin"),("staff","Staff")], db_index=True, default="user", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_email_verified", models.BooleanField(default=False)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_activity", models.DateTimeField(blank=True, null=True)),
                ("phone_number", encrypted_model_fields.fields.EncryptedCharField(blank=True, default="", max_length=20)),
                ("groups", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"db_table": "users", "verbose_name": "user", "verbose_name_plural": "users"},
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email", "is_active"], name="users_email_isactive_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["role", "is_active"], name="users_role_isactive_idx"),
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
                ("coach_mode", models.CharField(choices=[("mentor","Mentor"),("strict","Strict Coach"),("friendly","Friendly Guide"),("analytical","Analytical Advisor")], default="friendly", max_length=20)),
                ("timezone", models.CharField(default="UTC", max_length=50)),
                ("language", models.CharField(default="en", max_length=10)),
                ("personality_traits", models.JSONField(blank=True, default=dict)),
                ("behavior_patterns", models.JSONField(blank=True, default=dict)),
                ("productivity_windows", models.JSONField(blank=True, default=list)),
                ("communication_style", models.CharField(default="balanced", max_length=50)),
                ("onboarding_completed", models.BooleanField(default=False)),
                ("goals", models.JSONField(blank=True, default=list)),
                ("total_interactions", models.PositiveIntegerField(default=0)),
                ("ai_satisfaction_score", models.FloatField(default=0.0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "user_profiles"},
        ),
        migrations.CreateModel(
            name="UserDevice",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="devices", to=settings.AUTH_USER_MODEL)),
                ("device_fingerprint", models.CharField(db_index=True, max_length=64)),
                ("device_name", models.CharField(blank=True, max_length=200)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("is_trusted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "user_devices", "unique_together": {("user", "device_fingerprint")}},
        ),
    ]
