This package adds a media container for ATNewsItem content-types.

cienciasalud.newsmedia allows the final user to add images, videos, and regular
binary/text files into a media container that is attached to the content
object.

####### FIXME
- self.portal is the portal root
- self.folder is the current user's folder
- self.logout() "logs out" so that the user is Anonymous
- self.setRoles(['Manager', 'Member']) adjusts the roles of the current user
####### FIXME

First, we create a News Item called 'news-1' and store it in our user's folder.
We use Plone's content-type factory to create 'news-1', and we set a title and
description.
    >>> self.folder.invokeFactory('News Item', 'news-1')
    'news-1'
    >>> 'news-1' in self.folder
    True
    >>> news1 = self.folder['news-1']
    >>> news1.setTitle(u'Lorem ipsum news')
    >>> news1.setDescription(u'Donec bibendum gravida sapien, quis gravida quam laoreet vitae.')

Now that we have our News Item created and stored, we check if our news item has
a media container. It shouldn't.

    >>> from cienciasalud.newsmedia.newsmedia import IMediaContainer, IMediaManager
    >>> IMediaManager(news1).hasContainer() is False
    True
    >>> IMediaContainer(news1) is False
    True

    >>> IMediaManager(news1).createContainer()
    True
    >>> IMediaManager(news1).hasContainer() is True
    True

The next thing that we will do is to add an image file named "zptlogo.gif" into
our media container.
    >>> zptlogo = (
    ...     'GIF89a\x10\x00\x10\x00\xd5\x00\x00\xff\xff\xff\xff\xff\xfe\xfc\xfd\xfd'
    ...     '\xfa\xfb\xfc\xf7\xf9\xfa\xf5\xf8\xf9\xf3\xf6\xf8\xf2\xf5\xf7\xf0\xf4\xf6'
    ...     '\xeb\xf1\xf3\xe5\xed\xef\xde\xe8\xeb\xdc\xe6\xea\xd9\xe4\xe8\xd7\xe2\xe6'
    ...     '\xd2\xdf\xe3\xd0\xdd\xe3\xcd\xdc\xe1\xcb\xda\xdf\xc9\xd9\xdf\xc8\xd8\xdd'
    ...     '\xc6\xd7\xdc\xc4\xd6\xdc\xc3\xd4\xda\xc2\xd3\xd9\xc1\xd3\xd9\xc0\xd2\xd9'
    ...     '\xbd\xd1\xd8\xbd\xd0\xd7\xbc\xcf\xd7\xbb\xcf\xd6\xbb\xce\xd5\xb9\xcd\xd4'
    ...     '\xb6\xcc\xd4\xb6\xcb\xd3\xb5\xcb\xd2\xb4\xca\xd1\xb2\xc8\xd0\xb1\xc7\xd0'
    ...     '\xb0\xc7\xcf\xaf\xc6\xce\xae\xc4\xce\xad\xc4\xcd\xab\xc3\xcc\xa9\xc2\xcb'
    ...     '\xa8\xc1\xca\xa6\xc0\xc9\xa4\xbe\xc8\xa2\xbd\xc7\xa0\xbb\xc5\x9e\xba\xc4'
    ...     '\x9b\xbf\xcc\x98\xb6\xc1\x8d\xae\xbaFgs\x00\x00\x00\x00\x00\x00\x00\x00'
    ...     '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ...     '\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x06z@\x80pH,\x12k\xc8$\xd2f\x04'
    ...     '\xd4\x84\x01\x01\xe1\xf0d\x16\x9f\x80A\x01\x91\xc0ZmL\xb0\xcd\x00V\xd4'
    ...     '\xc4a\x87z\xed\xb0-\x1a\xb3\xb8\x95\xbdf8\x1e\x11\xca,MoC$\x15\x18{'
    ...     '\x006}m\x13\x16\x1a\x1f\x83\x85}6\x17\x1b $\x83\x00\x86\x19\x1d!%)\x8c'
    ...     '\x866#\'+.\x8ca`\x1c`(,/1\x94B5\x19\x1e"&*-024\xacNq\xba\xbb\xb8h\xbeb'
    ...     '\x00A\x00;'
    ...     )
    ...
    >>> from cienciasalud.newsmedia.newsmedia import MediaImage
    >>> zptimg = MediaImage(id='zptlogo.gif', title='Zope2 Logo', file=zptlogo, content_type='image/gif')
    >>> media = IMediaContainer(news1)
    >>> media[zptimg.id()] = zptimg
    >>> list(media)
    ['zptlogo.gif']
    >>> zpt = media['zptlogo.gif']
    >>> zpt.__dict__['data'] is str(zptlogo)
    True
    
    We can also edit the caption and the file data through our "zpt" image.

    >>> zpt.manage_edit(title='', content_type='', filedata='')
    >>> zpt.get_size() is 0 and zpt.title is ''
    True
    >>> zpt.getContentType() is ''
    True
    >>> zpt.manage_upload(zptlogo)
    >>> zpt.get_size()
    341
    >>> zpt.getContentType()
    'image/gif'
