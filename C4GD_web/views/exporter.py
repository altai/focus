from csv_staff import UnicodeWriter
from contextlib import closing
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from flask import make_response, jsonify


class BaseExporter(object):
    def __init__(self, data, columns, basename):
        self.data = data
        self.columns = columns
        self.basename = basename

    def wrap(self, content):
        #import pdb; pdb.set_trace()
        r = make_response(content)
        r.headers['Content-Disposition'] = 'attachment; filename=%s.%s' % (
            self.basename, self.extension)
        r.headers['Content-Type'] = self.mime
        return r


class JSONExporter(BaseExporter):
    extension = 'json'
    mime = 'application/json'

    def __call__(self):
        return self.wrap(jsonify(
            {
                'header': [(x.attr_name, x.verbose_name) for x in \
                               self.columns.selected],
                'body': self.data
                }))


class CSVExporter(BaseExporter):
    extension = 'csv'
    mime = 'text/csv'

    def __call__(self):
        with closing(StringIO()) as f:
            w = UnicodeWriter(f)
            w.writerow(["%s|%s" % (x.attr_name, x.verbose_name) for x in \
                            self.columns.selected])
            w.writerows([[str(j) for j in i] for i in self.data])
            return self.wrap(f.getvalue())


class XMLExporter(BaseExporter):
    extension = 'xml'
    mime = 'text/xml'

    def __call__(self):
        r = ET.Element('results')
        header = ET.SubElement(r, 'head')
        for x in self.columns.selected:
            ET.SubElement(
                header, 'name', 
                {'attr_name': x.attr_name, 'verbose_name': x.verbose_name})
        body = ET.SubElement(r, 'body')
        for data in self.data:
            row = ET.SubElement(body, 'row')
            for i, x in enumerate(data):
                ET.SubElement(
                    row,
                    self.columns.selected[i].attr_name,
                    {
                        'value': repr(x),
                        'type': type(x).__name__
                        #'picled': 
                        })
        with closing(StringIO()) as f:
            ET.ElementTree(r).write(f)
            result = self.wrap(f.getvalue())
        return result


class Exporter(object):
    def __init__(self, datatype, data, columns, basename):
        klass  = {
            'json': JSONExporter,
            'csv': CSVExporter,
            'xml': XMLExporter}[datatype]
        self.exporter = klass(data, columns, basename)

    def __call__(self):
        return self.exporter()

