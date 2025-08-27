from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, user_name, password=None, email=None, **extra_fields):
        if not user_name:
            raise ValueError('ユーザー名は必須です')
        email = self.normalize_email(email)
        user = self.model(user_name=user_name, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_name, password, email=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(user_name, password, email, **extra_fields)


class UserPersonal(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['email']
    USERNAME_FIELD = 'user_name'
    is_anonymous = False
    is_authenticated = True

    objects = UserManager()

    @property
    def id(self):
        return self.user_id

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    class Meta:
        db_table = 'user_table'


class Umamusume(models.Model):
    umamusume_id = models.AutoField(primary_key=True)
    umamusume_name = models.CharField(max_length=255)
    turf_aptitude = models.CharField(max_length=1)
    dirt_aptitude = models.CharField(max_length=1)
    front_runner_aptitude = models.CharField(max_length=1)
    early_foot_aptitude = models.CharField(max_length=1)
    midfield_aptitude = models.CharField(max_length=1)
    closer_aptitude = models.CharField(max_length=1)
    sprint_aptitude = models.CharField(max_length=1)
    mile_aptitude = models.CharField(max_length=1)
    classic_aptitude = models.CharField(max_length=1)
    long_distance_aptitude = models.CharField(max_length=1)

    class Meta:
        db_table = 'umamusume_table'


class UmamusumeActer(models.Model):
    acter_id = models.AutoField(primary_key=True)
    umamusume = models.OneToOneField(Umamusume, on_delete=models.CASCADE, db_column='umamusume_id')
    acter_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10)
    birthday = models.DateField()
    nickname = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'umamusume_acter_table'


class Live(models.Model):
    live_id = models.AutoField(primary_key=True)
    live_name = models.CharField(max_length=255)
    composer = models.CharField(max_length=255, blank=True, null=True)
    arranger = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'live_table'


class VocalUmamusume(models.Model):
    live = models.ForeignKey(Live, on_delete=models.CASCADE, db_column='live_id')
    umamusume = models.ForeignKey(Umamusume, on_delete=models.CASCADE, db_column='umamusume_id')

    class Meta:
        db_table = 'vocal_umamusume_table'


class Race(models.Model):
    race_id = models.AutoField(primary_key=True)
    race_name = models.CharField(max_length=255)
    race_state = models.IntegerField()  # 0: turf, 1: dirt
    distance = models.IntegerField()  # 1: sprint, 2: mile, 3: classic, 4: long
    distance_detail = models.SmallIntegerField(blank=True, null=True)
    num_fans = models.IntegerField(default=0)
    race_months = models.IntegerField()
    half_flag = models.IntegerField()  # 0: first half, 1: second half
    race_rank = models.IntegerField()
    junior_flag = models.IntegerField()
    classic_flag = models.IntegerField()
    senior_flag = models.IntegerField()
    scenario_flag = models.IntegerField(default=0)

    class Meta:
        db_table = 'race_table'


class ScenarioRace(models.Model):
    umamusume = models.ForeignKey(Umamusume, on_delete=models.CASCADE, db_column='umamusume_id')
    race = models.ForeignKey(Race, on_delete=models.CASCADE, db_column='race_id')
    race_number = models.IntegerField()
    random_group = models.IntegerField(blank=True, null=True)
    senior_flag = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'scenario_race_table'
        unique_together = ('umamusume', 'race', 'race_number')


class RegistUmamusume(models.Model):
    user = models.ForeignKey(UserPersonal, on_delete=models.CASCADE, db_column='user_id')
    umamusume = models.ForeignKey(Umamusume, on_delete=models.CASCADE, db_column='umamusume_id')
    regist_date = models.DateTimeField()
    fans = models.BigIntegerField()

    class Meta:
        db_table = 'regist_umamusume_table'
        unique_together = ('user', 'umamusume')


class RegistUmamusumeRace(models.Model):
    user = models.ForeignKey(UserPersonal, on_delete=models.CASCADE, db_column='user_id')
    umamusume = models.ForeignKey(Umamusume, on_delete=models.CASCADE, db_column='umamusume_id')
    race = models.ForeignKey(Race, on_delete=models.CASCADE, db_column='race_id')
    regist_date = models.DateTimeField()

    class Meta:
        db_table = 'regist_umamusume_race_table'
        unique_together = ('user', 'umamusume', 'race')


class Jewel(models.Model):
    user = models.ForeignKey(UserPersonal, on_delete=models.CASCADE, db_column='user_id')
    year = models.IntegerField()
    month = models.IntegerField()
    day = models.IntegerField()
    jewel_amount = models.IntegerField()

    class Meta:
        db_table = 'user_jewel_table'
        unique_together = ('user', 'year', 'month', 'day')
