#-*- coding:utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from sysu.secret.models import Weibouser, Weibo, Blacklist, Suggest
from sysu.secret.forms import UploadForm, handle_uploaded_file

from sysu.weibo.auth import OAuthHandler
from sysu.weibo.api import API
from sysu.weibo.error import WeibopError
from sysu.weibo import oauth
from sysu.weibo.binder import bind_api

import sae.storage
from datetime import datetime

consumer_key = getattr(settings, 'APP_KEY')
consumer_secret = getattr(settings, 'APP_SECRET')
CALLBACK_URL = 'http://sysusecret.sinaapp.com'

atoken={
        'daykey':'764ef964ae95350f809659d1160d960b',
        'daysecret': '17f022d3676b08aa36bae264337cf381',
        'nightkey': '55faad371683012b7cb265123a89586b',
        'nightsecret': '6ea051044838602665542b96adb2f061',
        'findkey': '788a644ac81dd0a83a5ac47d0377a3aa',
        'findsecret': 'e9423883743c4cc7d6934e75312be559',
    }

class WebOAuthHandler(OAuthHandler):
    def get_authorization_url_with_callback(self, callback, signin_with_weibo=False):
        try:
            self.request_token = self._get_request_token()
            
            if signin_with_weibo:
                url = self._get_request_token('authenticate')
            else:
                url = self._get_oauth_url('authorize')
            
            request = oauth.OAuthRequest.from_token_and_callback(
                token=self.request_token, callback=callback, http_url=url
            )
            return request.to_url()
        except Exception, e:
            raise WeibopError(e)
        
def _oauth():
    return WebOAuthHandler(consumer_key, consumer_secret)

def _get_referer_url(request):
    referer_url = request.META.get('HTTP_REFERER', '/')
    host = request.META['HTTP_HOST']
    if referer_url.startswith('http') and host not in referer_url:
        referer_url = '/'
    return referer_url

def log(request):
    back_to_url = _get_referer_url(request)
    request.session['login_back_to_url'] = back_to_url
    
    login_backurl = request.build_absolute_uri('/logincheck')
    auth_client = _oauth()
    auth_url = auth_client.get_authorization_url_with_callback(login_backurl)
    request.session['oauth_request_token'] = auth_client.request_token
    
    return HttpResponseRedirect(auth_url)

def log_check(request):
    verifier = request.GET.get('oauth_verifier', None)
    auth_client = _oauth()
    
    request_token = request.session['oauth_request_token']
    del request.session['oauth_request_token']
    
    auth_client.set_request_token(request_token.key, request_token.secret)
    access_token = auth_client.get_access_token(verifier)
    
    request.session['oauth_access_token'] = access_token
    
    back_to_url = request.session.get('login_back_to_url', '/')
    return HttpResponseRedirect(back_to_url)

def logout(request):
    try:
        del request.session['oauth_access_token']
    except KeyError:
        pass
    back_to_url = _get_referer_url(request)
    
    return HttpResponseRedirect(back_to_url)

def get_auth(request, select=0):
    auth = OAuthHandler(consumer_key, consumer_secret)
    if select == 1:
        auth.setToken(atoken['daykey'], atoken['daysecret'])
    elif select == 2:
        auth.setToken(atoken['nightkey'], atoken['nightsecret'])
    elif select == 3:
        auth.setToken(atoken['findkey'], atoken['findsecret'])
    elif select == 0:
        access_token = request.session.get('oauth_access_token', None)
        auth.setToken(access_token.key, access_token.secret)
    api = API(auth)
    return api

def get_friends(request):
    api = get_auth(request)
    friendlist = []
    try:
        followers = api.followers()
    except:
        return None

    for user in followers:
        f = {}
        f['id'] = user.id
        f['screen_name'] = user.screen_name
        f['description'] = user.description
        friendlist.append(f)
        
    return friendlist

def get_user(request):
    api = get_auth(request, 0)
    access_token = request.session.get('oauth_access_token', None)
    atkey = access_token.key
    atsecret = access_token.secret
    profile = {}
    me = api.me()
    try:
        user = api.get_user(user_id=me.id)
        profile['name'] = user.screen_name
        profile['id'] = user.id
        profile['atkey'] = atkey
        profile['atsecret'] = atsecret
        profile['profile'] = user.profile_image_url
        profile['followers'] = user.followers_count
        profile['statuses'] = user.statuses_count
    except WeibopError, e:
        raise e.reason
    return profile

def get_find_timeline(request):
    api = get_auth(request, 3)

    WeiboList = []
    timeline = api.user_timeline(count=2, page=1, uid=2635435174)
    for line in timeline:
        l = {}
        l['id'] = line.id
        l['text'] = line.text
        l['created'] = line.created_at
        WeiboList.append(l)

    return WeiboList[0]

def daynight_id():
    hour = datetime.now().hour
    if (hour>=6 and hour<20):
        userid = 2619983742
    else:
        userid = 2649316154
    return userid

def get_hole_timeline(request):
    api = get_auth(request, 1)
    weibolist = []
    hole_id = daynight_id()
    timeline = api.user_timeline(count=20, page=1, id=hole_id)
    for line in timeline:
        l = {}
        l['id'] = line.id
        l['text'] = line.text
        l['created'] = line.created_at
        weibolist.append(l)
    return render_to_response("weibolist.html",
        {'weibolist':weibolist,},
        context_instance=RequestContext(request)
    )

def get_comment(request, weiboid):
    api = get_auth(request, 1)
    path = '/statuses/show/' + str(weiboid) + '.json'
    get_status = bind_api( path = path, payload_type = 'status' )
    weibo = get_status(api)
    commentlist = []
    try:
        timeline = api.comments(id=weiboid)
    except WeibopError, e:
        return e.reason

    for line in timeline:
        c = {}
        c["id"] = line.id
        c["uid"] = line.user.id
        c["user"] = line.user.name.encode('utf-8')
        c["text"] = line.text.encode('utf-8')
        c["created"] = line.created_at
        commentlist.append(c)
    return render_to_response("weibo.html", {
        'weibo': weibo,
        'commentlist': commentlist,
        }, context_instance=RequestContext(request)
    )

def comment(request, weiboid):
    api = get_auth(request, 1)
    comment = request.POST.get('comment', '')
    if comment:
        try:
            weibo = api.comment(id=weiboid, comment=comment+u'#匿名评论＃')
            messages.warning(request, "成功评论")
        except WeibopError, e:
            messages.warning(request, "发送失败，请发送有意义的微博哦～")

    return HttpResponseRedirect(_get_referer_url(request))

def get_related(request):
    api = get_auth(request, 0)
    hour = datetime.now().hour
    userid = daynight_id()
    try:
        if (hour < 6 or hour > 20):
            source, target = api.show_friendship(target_id = userid)
            if not source.following:
                messages.warning(request, 
                    "关注中大夜洞，可方便您查看您所发微博的情况，请先关注本博")
                return False
            else:
                return True
        else:
            source, target = api.show_friendship(target_id = userid)
            if not source.following:
                messages.warning(request, 
                    "关注中大树洞，可方便您查看您所发微博的情况，请先关注本博")
                return False
            else:
                return True
    except WeibopError, e:
        raise e.reason

def get_blacklist(request):
    api = get_auth(request, 0)
    me = api.me()
    blackid = me.id
    try:
        b = Blacklist.objects.get(weiboid__exact=blackid)
        messages.warning(request, "不好意思，广告过滤或马甲禁言。。")
        flag = False 
    except Blacklist.DoesNotExist:
        flag = True
    return flag

@csrf_exempt
def cron_test(request):
    api = get_auth(request, 1)
    api.update_status(status='#中大树洞夜间剧场#越夜越精彩，现在切换至@中大夜洞 欢迎继续吐槽,  \
        明早6点会自动切换回来.相关寻物信息请关注@中大寻物 .发布端地址:http://t.cn/z0FEBnn')
    return HttpResponse("Hello Cron")

def get_info(request, content):
    user = get_user(request)
    try:
        weibouser = Weibouser.objects.get(weiboid=user['id'])
    except Weibouser.DoesNotExist:
        weibouser = Weibouser(name=user['name'], weiboid=user['id']）
        weibouser.save()
    weibo = Weibo(user=weibouser, weibo=content)
    weibo.save()
    yes = get_related(request) and get_blacklist(request)
    if yes:
        if user['followers'] < 30 and user['statuses'] < 20:
            messages.warning(request, "您好，不能用马甲发微博！")
            return False
        else:
            return True
    else:
        return False


def follow(request, userid):
    api = get_auth(request, 0)
    try:
        api.create_friendship(user_id=userid)
        messages.success(request, "关注成功!")
    except WeibopError, e:
        messages.warning(request, "您已经关注了!")
    
    return HttpResponseRedirect(_get_referer_url(request))

def suggest(request):
    comment = request.POST.get('comment', '')
    if comment:
        suggetst = Suggest(comment=comment)
        suggest.save()
        return HttpResponseRedirect(_get_referer_url(request))
    comments = Suggest.objects.all()
    return render_to_response("to_scnu.html",
        {'comments':comments},
        context_instance=RequestContext(request),
    )


def update(request, pic, content, is_find=None):
    hour = datetime.now().hour
    try:
        content = content.encode('utf-8')
         
        if is_find:
            api = get_auth(request, 3)
            try:
                if pic:
                    api.upload(filename=pic, status=content)
                else:
                    api.update_status(status=content)
                messages.success(request, "成功发布到中大寻物!")
            except WeibopError, e: 
                messages.warning(request, "怎么回事？发不到中大寻物！请联系一下树洞君！")
        
        if (hour>=6 and hour<20):
            api = get_auth(request, 1)
            try:
                if is_find:
                    try:
                        timeline = get_find_timeline(request)
                        weiboid = timeline['id']
                        #id为被转发的微博id，status为转发时添加的内容.
                        api.repost(id = weiboid, status = '')
                        messages.success(request, "中大树洞成功转发此寻物消息!")
                    except WeibopError, e:
                        raise e.reason;
                else:
                    if pic:
                        api.upload(filename=pic, status=content)
                    else:
                        api.update_status(status=content)
                    messages.success(request, "成功发布到中大树洞!")
            except WeibopError, e:
                messages.warning(request, "可能由于微博发布数量受限，发布失败，请晚上8点后再来尝试。")
        elif (hour<6 or hour>=20):
            api = get_auth(request, 2)
            try:
                if is_find:
                    try:
                        timeline = get_find_timeline(request)
                        weiboid = timeline['id']
                        #id为被转发的微博id，status为转发时添加的内容.
                        api.repost(id = weiboid, status = '')
                        messages.success(request, "中大夜洞成功转发此寻物消息!")
                    except WeibopError, e:
                        raise e.reason;
                else:
                    if pic:
                        api.upload(filename=pic, status=content)
                    else:
                        api.update_status(status=content)
                    messages.success(request, "成功发布到中大夜洞!")
            except WeibopError, e:
                messages.warning(request, "可能由于微博发布数量受限，发布失败，请明天早上再来尝试。")
        
    except (KeyError, ValueError):
        pass

def index(request):
    profile = {}
    form = UploadForm(request.POST or None, request.FILES or None)
    pic = ''
    if request.method == "POST":
        content = request.POST.get('weibo', '')
        is_find = request.POST.get('tofind', '')
        if form.is_valid():
            pic = handle_uploaded_file(request.FILES['pic'])

        if content:
            if len(content)>=2:
                yes = get_info(request, content)
                if yes:
                    update(request, pic, content, is_find)
                else:
                    return HttpResponseRedirect(_get_referer_url(request))
            else:
                messages.warning(request, "发送失败，请发送有意义的微博哦～")
                return HttpResponseRedirect(_get_referer_url(request))
        
    if request.session.get('oauth_access_token', None) is None:
        weibo_log = False
    else:
        weibo_log = True

        profile = {           
                'form': form,

            }
    log = {'weibo_log': weibo_log}
    profile.update(log)

    return render_to_response('home.html',
        profile,
        context_instance=RequestContext(request)
    )



