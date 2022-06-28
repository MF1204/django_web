from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.RESTRICT, related_name="profile")
    name = models.CharField(db_column='name', max_length=100)
    phone = models.CharField(db_column='phone', null=True, max_length=100, default='')
    department_id = models.ForeignKey('info_department', on_delete=models.RESTRICT, null=True, db_column='department_id')
    role_id = models.ForeignKey('info_role', on_delete=models.RESTRICT, null=False, db_column='role_id')
    usage_flag = models.CharField(db_column='usage_flag', max_length=10, default='1')

    class Meta:
        db_table = "profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile.objects.create(user=instance)
        # master.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    # instance.master.save()


class info_role(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    usage_flag = models.IntegerField(db_column='usage_flag', default=1)

    class Meta:
        db_table = "info_role"


class info_menu(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    usage_flag = models.IntegerField(db_column='usage_flag', default=1)

    class Meta:
        db_table = "info_menu"


class info_auth(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    usage_flag = models.IntegerField(db_column='usage_flag', default=1)

    class Meta:
        db_table = "info_auth"


class join_auth(models.Model):
    id = models.AutoField(primary_key=True)
    role_id = models.ForeignKey('info_role', on_delete=models.CASCADE, null=False, db_column='role_id')
    menu_id = models.ForeignKey('info_menu', on_delete=models.CASCADE, null=False, db_column='menu_id')
    auth_id = models.ForeignKey('info_auth', on_delete=models.CASCADE, null=False, db_column='auth_id')
    value = models.IntegerField(null=False, db_column='value', default=0)

    class Meta:
        db_table = "join_auth"


class info_factory(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = "info_factory"


class info_headquarter(models.Model):
    id = models.AutoField(primary_key=True)
    factory_id = models.ForeignKey('info_factory', on_delete=models.RESTRICT, db_column='factory_id')
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = "info_headquarter"


class info_department(models.Model):
    id = models.AutoField(primary_key=True)
    headquarter_id = models.ForeignKey('info_headquarter', on_delete=models.RESTRICT, null=True, db_column='headquarter_id')
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = "info_department"


class info_process(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    department_id = models.ForeignKey('info_department', on_delete=models.SET_NULL, null=True, db_column='department_id')
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = "info_process"


class info_equipment(models.Model):
    id = models.AutoField(primary_key=True)
    process_id = models.ForeignKey('info_process', on_delete=models.CASCADE, null=True, db_column='process_id')
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    profile_id = models.ForeignKey('profile', on_delete=models.SET_NULL, null=True, db_column='profile_id')
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = 'info_equipment'


class info_chamber(models.Model):
    id = models.AutoField(primary_key=True)
    equipment_id = models.ForeignKey('info_equipment', on_delete=models.CASCADE, null=False, db_column='equipment_id')
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = 'info_chamber'


class info_recipe(models.Model):
    id = models.AutoField(primary_key=True)
    chamber_id = models.ForeignKey('info_chamber', on_delete=models.CASCADE, null=False, db_column='chamber_id')
    code = models.CharField(db_column='code', max_length=10)
    name = models.CharField(db_column='name', max_length=20)
    revision = models.IntegerField(db_column='revision')
    register = models.ForeignKey('profile', on_delete=models.CASCADE, null=False, db_column='register')
    registdate = models.DateTimeField(db_column='registdate', auto_now=True)
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = 'info_recipe'


class info_dataset(models.Model):
    id = models.AutoField(primary_key=True)
    recipe_id = models.ForeignKey('info_recipe', on_delete=models.RESTRICT, db_column='recipe_id')
    static_path = models.CharField(db_column='static_path', max_length=255, default='')
    test_file_size = models.IntegerField(db_column='test_file_size')
    train_file_size = models.IntegerField(db_column='train_file_size')
    create_date = models.DateTimeField(db_column='create_date', auto_now=True)
    register = models.ForeignKey('profile', on_delete=models.RESTRICT, db_column='register')
    version = models.IntegerField(db_column='version')
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = 'info_dataset'

class info_training(models.Model):
    id = models.AutoField(primary_key=True)
    recipe_id = models.ForeignKey('info_recipe', on_delete=models.RESTRICT, db_column='recipe_id')
    traindata_size = models.IntegerField(db_column='traindata_size')
    testdata_size = models.IntegerField(db_column='testdata_size')
    static_path = models.CharField(db_column='static_path', max_length=255, default='')
    train_start = models.DateTimeField(db_column='train_start')
    train_end = models.DateTimeField(db_column='train_end')
    version = models.IntegerField(db_column='version')
    register = models.ForeignKey('profile', on_delete=models.RESTRICT, db_column='register')
    create_date = models.DateTimeField(db_column='create_date', auto_now=True)
    usage_flag = models.IntegerField(db_column='usage_flag')

    class Meta:
        db_table = 'info_training'


class mmProblem(models.Model):
    id = models.AutoField(primary_key=True)
    problem_name = models.CharField(db_column='problem_name', max_length=255, default='')
    model_func = models.CharField(db_column='model_func', max_length=255, default='')
    problem_note = models.CharField(db_column='problem_note', max_length=4096, default='')
    working_time = models.TimeField(db_column='working_time')
    created_at = models.DateTimeField(db_column='created_at', auto_now=True)
    delete_flag = models.CharField(db_column='delete_flag', max_length=10, default='0')

    class Meta:
        db_table = 'mm_problem'


class mmDataset(models.Model):
    id = models.AutoField(primary_key=True)
    equip_name = models.CharField(db_column='equip_name', max_length=50)
    chamber_name = models.CharField(db_column='chamber_name', max_length=50)
    recipe_name = models.CharField(db_column='recipe_name', max_length=50)
    revision_no = models.CharField(db_column='revision_no', max_length=50)
    data_static_path = models.CharField(db_column='data_static_path', max_length=255, default='')
    purpose = models.CharField(db_column='purpose', max_length=3, default='')
    data_name = models.CharField(db_column='data_name', max_length=255, default='')
    data_cnt = models.IntegerField(db_column='data_cnt', default='0')
    data_size = models.IntegerField(db_column='data_size', default='0')
    created_at = models.DateTimeField(db_column='created_at', auto_now=True)
    delete_flag = models.CharField(db_column='delete_flag', max_length=10, default='0')

    class Meta:
        db_table = 'mm_dataset'


class mmModel(models.Model):
    id = models.AutoField(primary_key=True)
    problem_id = models.IntegerField(db_column='problem_id')
    equipment_id = models.IntegerField(db_column='equipment_id')
    recipe_id = models.IntegerField(db_column='recipe_id')
    dataset = models.ForeignKey('mmDataset', on_delete=models.DO_NOTHING)
    sensor_cd = models.IntegerField(db_column='sensor_cd')
    model_name = models.CharField(db_column='model_name', max_length=255, default='')
    model_name_en = models.CharField(db_column='model_name_en', max_length=255, default='')
    user_id = models.IntegerField(db_column='user_id')
    created_at = models.DateTimeField(db_column='created_at', auto_now=True)
    delete_flag = models.CharField(db_column='delete_flag', max_length=10, default='0')
    threshold_train = models.FloatField(db_column='threshold_train')
    threshold_test = models.FloatField(db_column='threshold_test')
    num_anomaly_train = models.IntegerField(db_column='num_anomaly_train')
    num_anomaly_test = models.IntegerField(db_column='num_anomaly_test')
    train_start = models.DateTimeField(db_column='train_start')
    train_end_test_start = models.DateTimeField(db_column='train_end_test_start')
    test_end = models.DateTimeField(db_column='test_end')
    num_train = models.IntegerField(db_column='num_train')
    num_test = models.IntegerField(db_column='num_test')

    class Meta:
        db_table = 'mm_model'


class mhMonitoring(models.Model):
    id = models.AutoField(primary_key=True)
    model = models.ForeignKey('mmModel', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_column='created_at', auto_now=True)
    warnlist_path = models.CharField(db_column='warnlist_path', max_length=255, default='')
    user_id = models.IntegerField(db_column='user_id')
    delete_flag = models.CharField(db_column='delete_flag', max_length=10, default='0')

    class Meta:
        db_table = 'mh_monitoring'


class mmEquipspec(models.Model):
    id = models.AutoField(primary_key=True)
    equip_name = models.CharField(db_column='equip_name', max_length=50)
    chamber_cnt = models.IntegerField(db_column='chamber_cnt')
    sensor_cnt = models.IntegerField(db_column='sensor_cnt')

    class Meta:
        db_table = 'mm_equipspec'


class mmRecipe(models.Model):
    id = models.AutoField(primary_key=True)
    recipe_id = models.IntegerField(db_column='recipe_id')
    recipe_name = models.CharField(db_column='recipe_name', max_length=50)
    revision_no = models.CharField(db_column='revision_no', max_length=50)
    equip_name = models.CharField(db_column='equip_name', max_length=50)
    chamber_name = models.CharField(db_column='chamber_name', max_length=50)
    sensor_cd = models.IntegerField(db_column='sensor_cd')
    sensor_name = models.CharField(db_column='sensor_name', max_length=50)

    class Meta:
        db_table = 'mm_recipe'
