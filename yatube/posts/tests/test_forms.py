import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class FormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
            description='test_description',
        )

        cls.author = User.objects.create_user(
            username='JohnDoe',
            first_name='John',
            last_name='Doe',
            email='johndoe@yatube.com',
        )

        cls.post = Post.objects.create(
            text='test_text',
            author=cls.user,
            group=cls.group,
            id=51,
            image=cls.image,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка создания новой записи."""
        post = Post.objects.first()
        post.delete()
        posts_count = Post.objects.count()

        form_data = {
            'text': self.post.text,
            'author': self.user,
            'group': self.group.id,
            'image': self.post.image,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, form_data['image'])

    def test_form_update(self):
        """Проверка валидности редактирования поста."""
        posts_count = Post.objects.count()
        if posts_count == 1:
            old_post = get_object_or_404(Post, id=self.post.pk)
            another_group = Group.objects.create(
                title='Другая тестовая группа',
                slug='another_test_group'
            )
            form_data = {
                'text': 'Тестовый текст',
                'group': another_group.pk,
            }

            response = self.authorized_client.post(
                reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
                data=form_data,
                follow=False
            )
            self.assertEqual(Post.objects.count(), posts_count)
            self.assertRedirects(response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ))
            new_post = get_object_or_404(Post, id=self.post.pk)
            self.assertEqual(old_post.author, self.post.author)
            self.assertNotEqual(old_post.text, new_post.text)
            self.assertNotEqual(new_post.group.pk, self.post.group.pk)

            old_group_response = self.authorized_client.get(
                reverse('posts:group_list', args=(self.group.slug,))
            )
            self.assertTrue(
                old_group_response.context['page_obj'].paginator.count == 0)

            new_group_response = self.authorized_client.get(
                reverse('posts:group_list', args=(another_group.slug,))
            )
            self.assertTrue(
                new_group_response.context['page_obj'].paginator.count == 1)
