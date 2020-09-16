from rest_framework import (
    generics,
    permissions,
    authentication,
    status,
    viewsets,
    filters
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum

from .serializers import (
    UserSerializer,
    SettingSerializer,
    CategorySerializer,
    CategoryMemberShipSerializer,
    SectionSerializer,
    TaskSerializer,
    SubTaskSerializer,
    LabelSerializer,
    KarmaSerializer
)
from .models import (
    mUser,
    Week,
    mSetting,
    Category,
    mUserCategoryRelation,
    CategoryMemberShip,
    Section,
    Task,
    SubTask,
    Label,
    Karma,
)

from django.utils import timezone
from datetime import date

from .filters import (
    CategoryFilter,
    KarmaFilter,
)

from .mixins import (
    GetLoginUserMixin,
    CreateKarmaMixin,
)

import logging
logger = logging.getLogger(__name__)


class BaseModelViewSet(viewsets.ModelViewSet, GetLoginUserMixin, CreateKarmaMixin):

    def list(self, request, *args, **kwargs):
        self.set_auth0_id(request)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserViewSet(BaseModelViewSet):

    permission_classes = (permissions.AllowAny,)
    queryset = mUser.objects.all()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        logger.debug('=======================USER VIEW SET=====================')
        return super().list(request, *args, **kwargs)


class CategoryViewSet(BaseModelViewSet):

    permission_classes = (permissions.AllowAny,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_class = CategoryFilter

    def create(self, request, *args, **kwargs):
        self.auth0_id = request.data['auth0_id']
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            try:
                user = mUser.objects.get(auth0_id=request.data['auth0_id'])
                mUserCategoryRelation.objects.create(
                    user=user,
                    category=serializer.instance,
                    index=self.autoincrement(user),
                )

            except mUser.DoesNotExist:
                logger.error('mUserが見つかりませんでした。')
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except Category.DoesNotExist:
                logger.error('Categoryが見つかりませんでした。')
                return Response(status=status.HTTP_400_BAD_REQUEST)

            return Response(self.get_serializer(serializer.instance).data, status=status.HTTP_201_CREATED)

        logger.debug(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        self.auth0_id = request.data['auth0_id']
        queryset = self.queryset.get(pk=pk)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'], detail=False)
    def checkCategoryDuplication(self, request):
        '''
        カテゴリー作成時のカテゴリー名重複チェック
        '''
        auth0_id = request.query_params['auth0_id']
        name = request.query_params['name']
        try:
            user = mUser.objects.get(auth0_id=auth0_id)
            user_category = user.category_member.all()
            user_category.get(name=name)
        except Category.DoesNotExist:
            return Response({'status': 'success', 'result': True}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'success', 'result': False}, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def checkUpdateCategoryDuplication(self, request):
        '''
        カテゴリー更新時のカテゴリー名重複チェック
        '''
        auth0_id = request.query_params['auth0_id']
        current_name = request.query_params['current_name']
        new_name = request.query_params['new_name']

        user = mUser.objects.get(auth0_id=auth0_id)
        user_category = user.category_member.all()
        # 現在のカテゴリー名以外のカテゴリーを取得
        filter_category = user_category.exclude(name=current_name)
        if filter_category.filter(name=new_name).count() == 0:
            # 重複するカテゴリー名が存在しない
            return Response({'status': 'success', 'result': True}, status=status.HTTP_200_OK)
        return Response({'status': 'success', 'result': False}, status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=False)
    def update_category_index(self, request, pk=None):
        '''
        カテゴリーのDADでの並び替えアクション
        '''
        self.auth0_id = request.data['auth0_id']
        user = mUser.objects.get(auth0_id=request.data['auth0_id'])
        categorys = []
        for i, category in enumerate(request.data['categorys'], 1):
            cate = Category.objects.get(pk=category['id'])
            cate.index = i
            categorys.append(cate)

        Category.objects.bulk_update(categorys, fields=['index'])
        user_category = user.category_creator_user.filter(is_active=True).order_by('index')
        serializer = self.get_serializer(user_category, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def order_tasks(self, request, pk=None):
        '''
        並び替えボタンでのタスク並び替えアクション
        '''
        self.set_ordering_type(request)
        category = Category.objects.get(pk=pk)
        serializer = self.get_serializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=False)
    def change_categorys(self, request, pk=None):
        '''
        カテゴリー切り替え時のアクション

        request.data:
            - auth0_id : ログイン中のユーザーID
            - categorys : 選択されたカテゴリー一覧
        '''

        # ユーザー情報を取得
        self.auth0_id = request.data['auth0_id']
        user = mUser.objects.get(auth0_id=request.data['auth0_id'])
        user_categorys = user.category_creator_user.all()

        # ユーザーにまだ紐づいていないカテゴリーを作成する処理
        create_categorys = []
        for category in request.data['categorys']:
            if not user_categorys.filter(name=category['name']).exists():
                create_categorys.append(Category(
                    creator=user,
                    name=category['name'],
                    color=category['color'],
                    icon=category['icon'],
                    index=self.autoincrement(user)
                ))
        logger.info('追加で作成するカテゴリー')
        logger.info(create_categorys)
        Category.objects.bulk_create(create_categorys)

        # カテゴリーのis_activeを更新
        update_categorys = []
        for user_category in user_categorys:
            active_flg = False
            for category in request.data['categorys']:
                if user_category.name == category['name']:
                    # 選択されたカテゴリーなので有効フラグをTrueに変更
                    active_flg = True
                    break

            user_category.is_active = active_flg
            update_categorys.append(user_category)

        Category.objects.bulk_update(update_categorys, fields=['is_active'])
        res = user_categorys.filter(is_active=True).order_by('index')
        serializer = self.get_serializer(res, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def autoincrement(self, user):
        '''
        対象ユーザーが関与するカテゴリー総数 + 1を返却する
        '''
        res = user.category_creator_user.all().count() + 1
        return res

class SectionViewSet(BaseModelViewSet):

    permission_classes = (permissions.AllowAny,)
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(self.get_serializer(serializer.instance).data, status=status.HTTP_201_CREATED)

        logger.debug(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskViewSet(BaseModelViewSet):

    permission_classes = (permissions.AllowAny,)
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            user = mUser.objects.get(auth0_id=request.data['auth0_id'])
            self.create_karma(user, self.ADD_TASK)
            return Response(self.get_serializer(serializer.instance).data, status=status.HTTP_201_CREATED)

        logger.debug(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        self.perform_destroy(instance)
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def complete(self, request):
        """
        該当タスクの完了フラグを立てるアクション
            単体:
                key: complete_task_id
                value: 該当タスクのid
            複数:
                key: complete_task_id_list
                value: 該当タスクのidのリスト
        """
        if 'complete_task_id' in request.data:
            complete_task_id = request.data['complete_task_id']
            try:
                task = Task.objects.get(pk=complete_task_id)
                task.completed = True
                task.completed_at = timezone.datetime.now()
                task.save()
            except Task.DoesNotExist:
                logger.error('タスクが見つかりませんでした。')
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(self.get_serializer(task).data, status=status.HTTP_200_OK)

        else:
            complete_task_id_list = request.data['complete_task_id_list']
            complete_task_list = []
            try:
                for i in complete_task_id_list:
                    instance = Task.objects.get(pk=i)
                    instance.completed = True
                    instance.completed_at = timezone.datetime.now()
                    complete_task_list.append(instance)
                Task.objects.bulk_update(complete_task_list, ['completed', 'completed_at'])
            except Task.DoesNotExist:
                logger.error('タスクが見つかりませんでした。')
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(self.get_serializer(complete_task_list, many=True).data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def change_comment(self, request):
        """
        タスクのコメントを変更するアクション
        """
        try:
            task = Task.objects.get(pk=request.data['task_id'])
            task.comment = request.data['comment']
            task.save()
        except Task.DoesNotExist:
            logger.error('タスクが見つかりませんでした。')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(task).data, status=status.HTTP_200_OK)


class SubTaskViewSet(BaseModelViewSet):

    permission_classes = (permissions.AllowAny,)
    queryset = SubTask.objects.all()
    serializer_class = SubTaskSerializer

    def create(self, request, *args, **kwargs):

        logger.debug("create")
        logger.debug(request.data)
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(self.get_serializer(serializer.instance).data, status=status.HTTP_201_CREATED)

        logger.debug(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=False)
    def complete(self, request):
        """
        該当サブタスクの完了フラグを立てるアクション
            完了したサブタスクIDリストを返す
            ※既に完了したものも送られてくる可能性があるため、サブタスクを一括更新
        """
        task_id = request.data['task_id']
        compelete_sub_task_id_list = request.data['compelete_sub_task_id_list']
        sub_task_list = []
        # complete_sub_task_list = []
        try:
            task = Task.objects.get(pk=task_id)
            subTasks = task.subtask_target_task.all().iterator()
            for subTask in subTasks:
                if subTask.id in compelete_sub_task_id_list:
                    subTask.completed = True
                    if subTask.completed_at == None: subTask.completed_at = timezone.datetime.now()
                    # complete_sub_task_list.append(subTask)
                else:
                    subTask.completed = False
                    subTask.completed_at = None
                sub_task_list.append(subTask)
            SubTask.objects.bulk_update(sub_task_list, ['completed', 'completed_at'])
        except Task.DoesNotExist:
            logger.error('タスクが見つかりませんでした。')
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'target_task': task_id,
            'sub_task_list': compelete_sub_task_id_list
        }, status=status.HTTP_200_OK)


class LabelViewSet(BaseModelViewSet):

    permission_classes = (permissions.AllowAny,)
    queryset = Label.objects.all()
    serializer_class = LabelSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(self.get_serializer(serializer.instance).data, status=status.HTTP_201_CREATED)

        logger.debug(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KarmaViewSet(BaseModelViewSet):

    permission_classes = (permissions.AllowAny,)
    queryset = Karma.objects.all()
    serializer_class = KarmaSerializer
    filter_class = KarmaFilter

    @action(methods=['GET'], detail=False)
    def result(self, request, pk=None):
        user = mUser.objects.get(auth0_id=request.query_params['auth0_id'])

        # 1日のタスク量を取得
        setting = mSetting.objects.get(target_user=user)
        daily_task_number = setting.daily_task_number

        today_comp_task_count = user.task_target_user.filter(completed=True, completed_at__date=date.today()).count()

        total_result = Karma.objects.filter(target_user=user).aggregate(sum_of_point=Sum('point'))
        # カルマポイントがない場合は0を入れる
        total = total_result['sum_of_point'] if total_result['sum_of_point'] != None else 0
        info = self.get_karma_info(total)
        data = {
            'today_comp_task_count': today_comp_task_count,
            'daily_task_number': daily_task_number,
            'rank': info['rank'],
            'msg': info['msg'],
            'totalPoint': total,
        }
        return Response(data=data, status=status.HTTP_200_OK)

    def get_karma_info(self, point):
        if point < 100:
            return { 'rank': '初心者', 'msg': 'あなたは初心者だ'}
        elif point < 200:
            return { 'rank': '中級者', 'msg': 'あなたは中級者なのです'}
        elif point < 300:
            return { 'rank': '上級者', 'msg': 'あなたは上級者だ。頑張れ'}
        else:
            return { 'rank': 'マスター', 'msg': 'あなたはマスターしてる。さらに頑張れ'}
