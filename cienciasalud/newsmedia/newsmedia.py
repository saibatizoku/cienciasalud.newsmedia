import datetime
import pytz
import urllib
import math

from five import grok
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from plone.app.layout.viewlets.interfaces import IAboveContentBody
#from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from Acquisition import Implicit
from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.ATContentTypes.interfaces import IATNewsItem

from zope.component import getMultiAdapter
from zope.interface import Interface
from zope.schema import BytesLine
from zope.schema import Bytes
from zope.schema import TextLine
from zope.container.interfaces import INameChooser
from plone.i18n.normalizer import filenamenormalizer

from OFS.Image import File
from OFS.Image import Image
from cStringIO import StringIO

try:
    import PIL.Image
except ImportError:
    # no PIL, no scaled versions!
    HAS_PIL = False
    PIL_ALGO = None
else:
    HAS_PIL = True
    PIL_ALGO = PIL.Image.ANTIALIAS

_marker = []

video_mimetypes = ['video/mp4', 'video/x-flv']
image_mimetypes = ['image/jpeg', 'image/gif', 'image/png']

# GLOBAL CONTEXT INTERFACES IS IATNewsItem
grok.context(IATNewsItem)

# INTERFACES
class INewsMediaLayer(IDefaultBrowserLayer):
   """ Default Layer for News Media Items """

class IMediaManager(Interface):
    """ Marker interface for news-item media. """

class IMediaContainer(Interface):
    """ Marker interface for a news-item media container. """

class IFile(Interface):
    title = TextLine(
            title = u'Titulo de la imagen',
            default=u'',
            missing_value=u'',
            required=False,
            )

    data = Bytes(
            title=u'Image',
            description=u'The actual content of the object.',
            default='',
            missing_value='',
            required=False,
            )

class IImage(IFile):
    """ Marker Interface for Image files. """

class IVideo(IFile):
    """ Marker Interface for Video files. """

# CONTENT-TYPES
class NewsMediaContainer(Implicit, grok.Container):
    grok.implements(IMediaContainer)
    id = __name__ = 'media'

class MediaFile(File):
    grok.implements(IFile)

class MediaImage(Image):
    grok.implements(IImage)

class MediaVideo(File):
    grok.implements(IVideo)

# ADAPTERS
@grok.adapter(IATNewsItem)
@grok.implementer(IMediaContainer)
def news_to_media(news_item):
    if IMediaManager(news_item).hasContainer():
        return IMediaManager(news_item).getMediaContainer()
    return False

class MediaManager(grok.Adapter):
    grok.provides(IMediaManager)
    grok.context(IATNewsItem)

    def __init__(self, context):
        self.context = context

    def hasContainer(self):
        media = getattr(self.context, 'media', None)
        return media is not None

    def createContainer(self):
        if not 'media' in self.context.__dict__:
            media = NewsMediaContainer()
            self.context.__dict__['media'] = media
            return True
        return

    def getContents(self):
        if not self.hasContainer():
            return []
        return self.context.media.keys()

    def getMediaContainer(self):
        if self.hasContainer():
            return self.context.media
        return

# VIEWS
class MediaContainerView(grok.View):
    grok.context(IMediaContainer)
    grok.name('index')
    grok.require('zope2.View')
    grok.layer(INewsMediaLayer)

    def update(self):
        self.redirect(self.url(self.context.__parent__))

    def render(self):
        return u''

class AddFileForm(grok.AddForm):
    grok.name(u'add_media')
    grok.require('cmf.AddPortalContent')
    grok.layer(INewsMediaLayer)
    #grok.template('default_edit_form')

    form_fields = grok.AutoFields(IImage).select('data')

    def getContents(self):
        return self.context

    @grok.action(u'Subir archivo')
    def add(self, **data):
        if len(data['data']) > 0:
            self.upload(**data)
        self.redirect(self.url(self.context)+'/add_media')

    def upload(self, **data):
        fileupload = self.request['form.data']
        if fileupload and fileupload.filename:
            contenttype = fileupload.headers.get('Content-Type')
            asciiname = filenamenormalizer.normalize(text=fileupload.filename, locale=self.request.locale.getLocaleID())
            mediacontainer = IMediaContainer(self.context)
            filename = INameChooser(mediacontainer).chooseName(asciiname, None)
            caption = filename
            #if not data['title']:
            #    caption = filename
            #else:
            #    caption = data['title']
            if contenttype in video_mimetypes:
                file_ = MediaVideo(filename, caption, data['data'], contenttype)
            elif contenttype in image_mimetypes:
                file_ = MediaImage(filename, caption, data['data'], contenttype)
            else:
                file_ = MediaFile(filename, caption, data['data'], contenttype)
            mediacontainer[filename] = file_

class DeleteMedia(grok.View):
    grok.require('zope2.DeleteObjects')
    grok.layer(INewsMediaLayer)

    def render(self):
        filename = urllib.unquote(self.request.get('QUERY_STRING'))
        if filename and filename in self.context['media']:
            del self.context['media'][filename]
            self.redirect(self.url(self.context, 'add_media'))

class EditImageForm(grok.EditForm):
    grok.context(IImage)
    grok.name(u'edit')
    grok.require('cmf.ModifyPortalContent')
    grok.layer(INewsMediaLayer)
    grok.template('default_edit_form')

    form_fields = grok.AutoFields(IImage)

class BaseVideoView(grok.View):
    grok.baseclass()
    grok.context(MediaVideo)
    grok.layer(INewsMediaLayer)
    size = ()

    def render(self):
        return self.context.index_html(self.request, self.response)

class BaseImageView(grok.View):
    grok.baseclass()
    grok.context(MediaImage)
    grok.layer(INewsMediaLayer)
    size = ()

    def render(self):
        thumb, format = self.scale(*self.size)
        img = self._make_image(file=thumb, format=format)
        imgd = img.__of__(aq_parent(aq_inner(self.context)))
        return imgd.index_html(self.request, self.response)

    def _make_image(self, file='', format=''):
        """Image content factory"""
        id = self.context.__name__
        title = self.context.title
        mimetype = 'image/%s' % format.lower()
        return MediaImage(id, title, file, mimetype)

    def scale(self, w, h, default_format = 'PNG'):
        """ scale image (with material from ImageTag_Hotfix)"""
        #make sure we have valid int's
        size = int(w), int(h)
        data = str(self.context.data)

        original_file=StringIO(data)
        image = PIL.Image.open(original_file)
        # consider image mode when scaling
        # source images can be mode '1','L,','P','RGB(A)'
        # convert to greyscale or RGBA before scaling
        # preserve palletted mode (but not pallette)
        # for palletted-only image formats, e.g. GIF
        # PNG compression is OK for RGBA thumbnails
        original_mode = image.mode
        if original_mode == '1':
            image = image.convert('L')
        elif original_mode == 'P':
            image = image.convert('RGBA')
        image.thumbnail(size, PIL_ALGO)
        format = image.format and image.format or default_format
        # decided to only preserve palletted mode
        # for GIF, could also use image.format in ('GIF','PNG')
        if original_mode == 'P' and format == 'GIF':
            image = image.convert('P')
        thumbnail_file = StringIO()
        # quality parameter doesn't affect lossless formats
        image.save(thumbnail_file, format, quality=88)
        thumbnail_file.seek(0)
        return thumbnail_file, format.lower()

class ImageThumbView(BaseImageView):
    grok.name('thumb')
    grok.require('zope2.View')
    size = (90, 90)

class ImageLargeView(BaseImageView):
    grok.name('large')
    grok.require('zope2.View')
    size = (768, 768)

class ImageMiniView(BaseImageView):
    grok.name('mini')
    grok.require('zope2.View')
    size = (192, 192)

# VIEWLETS
class MediaViewletManager(grok.ViewletManager):
    grok.name('newsitem.media')
    grok.require('zope2.View')

class AddMediaViewlet(grok.Viewlet):
    grok.viewletmanager(MediaViewletManager)
    grok.require('zope2.View')
    grok.layer(INewsMediaLayer)

    def update(self):
        self.form = getMultiAdapter((self.context, self.request), name='add_media')
        self.form.update_form()
        if self.request.method == 'POST':
            app = grok.get_application(self.context)
            self.__parent__.redirect(self.__parent__.url(obj=app))

    def render(self):
        return self.form.render()

class BaseViewlet(grok.Viewlet):
    grok.viewletmanager(IAboveContentBody)
    grok.template('baseviewlet')
    grok.require('zope2.View')
    grok.layer(INewsMediaLayer)

    def update(self):
        newsmedia = IMediaManager(self.context)
        self.newsmedia = newsmedia

    def imageRows(self, cols, keys):
        rows = []
        if not cols or not keys:
            return rows
        rows_number = int(math.ceil(float(len(keys))/float(cols)))
        for row in range(rows_number):
            this_row = []
            start = row*int(cols)
            end = start + int(cols) 
            for key in keys[start:end]:
                this_row.append(key)
            rows.append(this_row)
        return rows

    def is_image(self, key):
        media = self.newsmedia.getMediaContainer()
        return isinstance(media[key], MediaImage)

    def is_video(self, key):
        media = self.newsmedia.getMediaContainer()
        return isinstance(media[key], MediaVideo)
