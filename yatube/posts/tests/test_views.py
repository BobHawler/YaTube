import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm

from ..models import Comment, Follow, Group, Post

User = get_user_model()

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

UPLOADED_GIF = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='test_description',
        )
        cls.group_with_no_posts = Group.objects.create(
            title='Тестовый заголовок для группы без постов',
            slug='no_posts_slug',
            description='Тестовое описание для группы без постов'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
            image=UPLOADED_GIF
        )
        cls.author = User.objects.create_user(
            username='authorForPosts',
            first_name='John',
            last_name='Doe',
            email='testuser@yatube.ru'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='JohnDoe')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': self.user}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.pk}),
            'posts/create_post.html': reverse('posts:post_edit',
                                              kwargs={'post_id':
                                                      self.post.pk}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index передается с соответствующим контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_text_0 = {
            response.context['post'].text: self.post.text,
            response.context['post'].author: self.user.username,
            response.context['post'].group: self.group
        }

        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)
        self.assertTrue(self.post.image)

    def test_group_post_show_correct_context(self):
        """Шаблон group_post передается с соответсвующим контекстом."""
        response = self.authorized_client.get(reverse
                                              ('posts:group_list',
                                               kwargs={'slug':
                                                       self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertTrue(self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile передается с соответствующим контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username':
                                                      self.post.author.username
                                                      }))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertTrue(self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail передается с соответсвующим контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id':
                                                              self.post.id}))
        first_object = response.context['post']
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author.posts.count(),
                         self.post.author.posts.count())
        self.assertTrue(self.post.image)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create передается с соответствующим контекстом."""
        response = self.authorized_client.get(reverse(
                                              'posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertIn('form', response.context)
                self.assertNotIn('is_edit', response.context)

        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit передается с соответствующим контекстом."""
        response = self.authorized_author.get(reverse('posts:post_edit',
                                                      kwargs={'post_id':
                                                              self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_post_in_index_group_list_profile_exists(self):
        """Новый пост отображается на страницах index, group_list, profile."""
        urls_list = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username':
                                             self.post.author.username}),
        )
        for tested_url in urls_list:
            response = self.authorized_author.get(tested_url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_post_is_not_in_other_group(self):
        """Поста нет в непредназначенной группе."""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group_with_no_posts.slug}))
        posts = response.context['page_obj']
        self.assertEqual(0, len(posts))

    def test_auth_can_write_comments(self):
        """Авторизованный пользователь может оставлять комментарии."""
        form_data = {
            'post': self.post,
            'author': self.user,
            'text': 'TESTTEXT'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(self.post.comments.count(), 1)
        self.assertEqual(comment.post, self.post)

    def test_guest_cannot_write_comment(self):
        """Неавторизованный пользователь не может писать комментарии."""
        form_data = {
            'test': 'Тестовый комментарий'
        }
        response_guest = self.guest_client.post(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        response_auth = self.authorized_client.post(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response_guest.status_code, 302)
        self.assertEqual(response_auth.status_code, 200)

    def test_cach_in_index_page(self):
        """Тест работы кэша на странице index."""
        response = self.authorized_client.get(reverse('posts:index'))
        before_clearing_the_cache = response.content

        Post.objects.create(
            group=self.group,
            text='Новый текст, после кэша',
            author=self.user
        )

        cache.clear()

        response = self.authorized_client.get(reverse('posts:index'))
        after_clearing_the_cache = response.content
        self.assertNotEqual(before_clearing_the_cache,
                            after_clearing_the_cache)

    def test_login_user_follow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей.
        """
        followers_before = len(
            Follow.objects.all().filter(author_id=self.author.id)
        )
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author]))
        followers_after = len(
            Follow.objects.all().filter(author_id=self.author.id))
        self.assertEqual(followers_after, followers_before + 1)

    def test_login_user_unfollow(self):
        """
        Авторизованный пользователь может отписываться
        от других пользователей.
        """
        followers_before = len(
            Follow.objects.all().filter(author_id=self.author.id))
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author]))
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=[self.author]))
        followers_after = len(
            Follow.objects.all().filter(author_id=self.author.id))
        self.assertEqual(followers_before, followers_after)

    def test_post_in_follow(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан.
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author]))

        response_after_follow = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(response.content, response_after_follow.content)

    def test_not_following_after(self):
        """
        Новая запись пользователя не появляется в ленте тех,
        кто не подписан на него.
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='JohnDoe')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Test description'
        )
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i+1}',
                author=cls.author,
                group=cls.group
            ))
        Post.objects.bulk_create(cls.posts)

    def test_paginator(self):
        """Тест паджинатора"""
        urls_list = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        }
        for tested_url in urls_list:
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context.get('page_obj'
                                                      ).object_list), 10)

        for tested_url in urls_list:
            response = self.client.get(tested_url, {'page': 2})
            self.assertEqual(len(response.context.get('page_obj'
                                                      ).object_list), 3)
