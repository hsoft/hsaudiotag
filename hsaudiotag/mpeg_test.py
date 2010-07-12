# Created By: Virgil Dupras
# Created On: 2005/02/05
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)

# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

import unittest
import io

from . import mpeg
from .squeeze import expand_mpeg
from .testcase import TestCase

class TCMpeg(TestCase):
    def test1(self):
        """
        test1.mp3: a mpeg file with a id3v2 tag at the start of the file with a size
        of 0x800, but the first frame header is only at 0x9a1. There is also a
        id3v1 tag at the end of the file.
        """
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/test1.mp3')))
        self.assertEqual(m.size,2355703)
        self.assertEqual(m.bitrate,128)
        self.assertEqual(m.duration,147)
        self.assert_(m.id3v1.exists)
        self.assert_(m.id3v2.exists)
        self.assert_(m.tag is m.id3v2)
        self.assertEqual(m.audio_offset,0x9a1)
        self.assertEqual(m.audio_size,m.size - 128 - 0x9a1)
        self.assertEqual(44100,m.sample_rate)
    
    def test2(self):
        """
        test2.mp3: same as test 1, but with the id3v2 tag removed
        (The first frame is at 0x1a1). The id3v1 tag is ALSO removed.
        """
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/test2.mp3')))
        self.assertEqual(m.size,2353527)
        self.assertEqual(m.bitrate,128)
        self.assertEqual(m.duration,147)
        self.assert_(not m.id3v1.exists)
        self.assert_(not m.id3v2.exists)
        self.assertEqual(m.audio_offset,0x1a1)
        self.assertEqual(m.audio_size,m.size - 0x1a1)
    
    def test3(self):
        """
        test3.mp3: A normal mpeg file, with no tag at the start, and the first frame
        begins at the first byte. There is a v1 tag at the end
        """
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/test3.mp3')))
        self.assertEqual(m.size,2701840)
        self.assertEqual(m.bitrate,128)
        self.assertEqual(m.duration,168)
        self.assert_(m.id3v1.exists)
        self.assert_(not m.id3v2.exists)
        self.assert_(m.tag is m.id3v1)
        self.assertEqual(m.audio_offset,0)
        self.assertEqual(m.audio_size,m.size - 128)
    
    def test4(self):
        """
        test4.mp3: A normal mpeg file, with an id3v2 tag at the start, and the size of
        the tag is reported correctly, which means that the first frame header starts at
        the end of the tag. This file has a id3v1 tag.
        """
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/test4.mp3')))
        self.assertEqual(m.size,2702480)
        self.assertEqual(m.bitrate,128)
        self.assertEqual(m.duration,168)
        self.assert_(m.id3v1.exists)
        self.assert_(m.id3v2.exists)
        self.assertEqual(m.audio_offset,0x200)
        self.assertEqual(m.audio_size,m.size - 0x200 - 128)
    
    def test5(self):
        """
        test5.mp3: test3.mp3, but instead of starting with 0xfffb (a valid 2 bytes start
        for a frame header), it starts with 0xffb0, which is not a valid header. The
        second header is 0xffe00000, which is a valid header, but will result in a
        bitrate of 0, and thus, a ZeroDizision error, which is supposed to be catched,
        and invalidate the frame (which brings us to the 3rd frame header, which is
        valid, and it's the one that will be used.
        """
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/test5.mp3')))
        self.assertEqual(m.size,2701840)
        self.assertEqual(m.bitrate,128)
        self.assertEqual(m.duration,168)
        self.assert_(m.id3v1.exists)
        self.assert_(not m.id3v2.exists)
        self.assert_(m.tag is m.id3v1)
        self.assertEqual(m.audio_offset,0x1a1)
        self.assertEqual(m.audio_size,m.size - 0x1a1 - 128)
    
    def test6(self):
        """
        test6.mp3: Infected Mushroom, My Mummy Said. It's a VBR. iTunes says it has an avg 
        bitrate of 202, and a duration of 7:23 (443 sec).
        """
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/test6.mp3')))
        self.assert_(m.vbr)
        self.assertEqual(m.size,11198817)
        self.assertEqual(m.bitrate,202)
        self.assertEqual(m.duration,443)
        self.assert_(m.id3v1.exists)
        self.assert_(m.id3v2.exists)
        self.assert_(m.tag is m.id3v2)
    
    def testwith_footer(self):
        """
        with_footer.mp3 is a mpeg with a tag at the end of the file. mpeg info
        should be extracted without problem in this event. The length of the
        tag is 0x20a
        """
        m = mpeg.Mpeg(expand_mpeg(self.filepath('id3v2/with_footer.mp3')))
        self.assertEqual(m.size,2702234)
        self.assertEqual(m.bitrate,128)
        self.assertEqual(m.duration,168)
        self.assert_(not m.id3v1.exists)
        self.assert_(m.id3v2.exists)
        self.assertEqual(m.audio_offset,0)
        self.assertEqual(m.audio_size,m.size - 0x20a)
    
    def testZeroFile(self):
        m = mpeg.Mpeg(self.filepath('zerofile'))
        self.assertEqual(m.size,0)
        self.assertEqual(m.bitrate,0)
        self.assertEqual(m.duration,0)
        self.assert_(not m.id3v1.exists)
        self.assert_(not m.id3v2.exists)
        self.assertEqual(m.audio_offset,0)
        self.assertEqual(m.audio_size,0)
    
    def test7(self):
        #The problem with this file is that there is some junk at the start of the
        #file, so seek_first_fram has to be called, and seek_first_frame doesn't put the
        #fp back to a good position, thus, messing with the vbr thereafter.
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/test7.mp3')))
        self.assert_(m.vbr)
        self.assertEqual(m.bitrate,172)
        self.assertEqual(m.duration,182)
        self.assert_(m.id3v1.exists)
        self.assert_(not m.id3v2.exists)
        
    def test8(self):
        #The file has garbage at the end, thus making the duration 5:12 when it's actually
        #4:59. The id3v2 tag has a TLEN frame, which we must use instead of calculating duration.
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/test8.mp3')))
        self.assertEqual(m.duration,299)
    
    def test_double_id3(self):
        #This file has 2 ID3v2 tags with one garbage char in the middle of them. CBR
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/double_id3.mp3')))
        self.assertEqual(m.duration,203)
        self.assertEqual(128,m.bitrate)
    
    def test_vbr_without_header(self):
        #Same as test6, but with the Xing header frame removed.
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/vbr_without_header.mp3')))
        self.assert_(m.vbr)
        self.assertEqual(m.bitrate,202)
        self.assertEqual(m.duration,443)
        self.assert_(m.id3v1.exists)
        self.assert_(m.id3v2.exists)
        
    def test_vbr_fhg(self):
        m = mpeg.Mpeg(expand_mpeg(self.filepath('mpeg/vbr_fhg.mp3')))
        self.assert_(m.vbr)
        self.assertEqual(m.bitrate,221)
        self.assertEqual(m.duration,194)
    
    def test_tell_returns_None(self):
        #See TCFrameBrowser test with the same name for comments
        fp = io.BytesIO(b'')
        fp.tell = lambda:None
        m = mpeg.Mpeg(fp)
        self.assertEqual(0,m.size)
    
    def test_tag_duration_different(self):
        """the tag reports a duration of 29 seconds, but the data actually contains 1 real second
        with garbage at the end."""
        m = mpeg.Mpeg(self.filepath('mpeg/tag_duration_different.mp3'))
        self.assertEqual(m.duration, 1)
    

class TCFrameBrowser(TestCase):
    def test_valid_first_frame_and_no_tag(self):
        fp = expand_mpeg(self.filepath('mpeg/test3.mp3'))
        b = mpeg.FrameBrowser(fp)
        self.assertEqual(0,b.frame_index)
        self.assertEqual(128,b.frame.bitrate)
        self.assertEqual(128,next(b).bitrate)
        self.assertEqual(1,b.frame_index)
        fp.close()
    
    def test_must_seek_first_frame(self):
        fp = expand_mpeg(self.filepath('mpeg/test2.mp3'))
        b = mpeg.FrameBrowser(fp)
        self.assertEqual(128,b.frame.bitrate)
        self.assertEqual(128,next(b).bitrate)
        fp.close()
    
    def test_stop_going_foward_when_frame_is_invalid(self):
        fp = expand_mpeg(self.filepath('mpeg/test2.mp3'))
        b = mpeg.FrameBrowser(fp)
        while next(b).valid:
            pass
        i = b.frame_index
        next(b)
        self.assertEqual(i,b.frame_index)
        fp.close()
    
    def test_update_position_on_next(self):
        fp = expand_mpeg(self.filepath('mpeg/test2.mp3'))
        b = mpeg.FrameBrowser(fp)
        p = b.position
        next(b)
        self.assert_(b.position > p)
        fp.close()
    
    def test_First(self):
        fp = expand_mpeg(self.filepath('mpeg/test6.mp3'))
        b = mpeg.FrameBrowser(fp)
        first_br = b.frame.bitrate
        next(b)
        self.assertEqual(first_br,b.first().bitrate)
        self.assertEqual(0,b.frame_index)
        fp.close()
    
    def test_seek_with_id3_tag_in_the_way(self):
        #What must happen is that is __Seek finds 'ID3' in it's
        #seek data, it must abort it's current seeking, skip fp to after
        #the tag, and recall __Seek
        fp = expand_mpeg(self.filepath('mpeg/double_id3.mp3'))
        b = mpeg.FrameBrowser(fp)
        self.assert_(b.frame.valid)
        fp.close()
    
    def test_zerofile(self):
        fp = open(self.filepath('zerofile'),'rb')
        b = mpeg.FrameBrowser(fp)
        self.assertEqual(0,b.frame_index)
        self.assert_(not b.frame.valid)
        self.assertEqual(0,b.position)
        fp.close()
    
    def test_tell_returns_None(self):
        #I remember when I was building this TC that tell() returned
        #None once. So I added code to work around this. But then, some time later,
        #I removed that code, and the test units continued to work A-OK. I *know* it can
        #happen. Thus, I fake it here because I can't find what conditions makes this possible.
        fp = io.BytesIO(b'')
        fp.tell = lambda:None
        b = mpeg.FrameBrowser(fp)
        self.assertEqual(0,b.position)
    
    def test_stats_on_one_second(self):
        """one_second has exactly one second worth of mpeg frames (39 * 417 bytes @ 128)"""
        fp = open(self.filepath('mpeg/one_second.mp3'), 'rb')
        b = mpeg.FrameBrowser(fp)
        fcount, size = b.stats()
        self.assertEqual(fcount, 39)
        self.assertEqual(size, 39 * 417)
    

if __name__ == "__main__":
    unittest.main()
