# coding=utf-8
import contextlib
import StringIO
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import flask

from focus.views import csv_staff


class BaseExporter(object):
    def __init__(self, data, columns, basename):
        self.data = data
        self.columns = columns
        self.basename = basename

    def wrap(self, content):
        r = flask.make_response(content)
        r.headers['Content-Disposition'] = 'attachment; filename=%s.%s' % (
            self.basename, self.extension)
        r.headers['Content-Type'] = self.mime
        return r


class JSONExporter(BaseExporter):
    extension = 'json'
    mime = 'application/json'

    def __call__(self):
        return self.wrap(flask.jsonify(
            {
                'header': [(x.attr_name, x.verbose_name) for x in
                           self.columns.selected],
                'body': self.data
            }))


class CSVExporter(BaseExporter):
    extension = 'csv'
    mime = 'text/csv'

    def __call__(self):
        with contextlib.closing(StringIO.StringIO()) as f:
            w = csv_staff.UnicodeWriter(f)
            w.writerow(
                map(
                    lambda x: "%s|%s" % (x.attr_name, x.verbose_name),
                    self.columns.selected))
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
        with contextlib.closing(StringIO.StringIO()) as f:
            ET.ElementTree(r).write(f)
            result = self.wrap(f.getvalue())
        return result


class Exporter(object):
    def __init__(self, datatype, data, columns, basename):
        klass = {
            'json': JSONExporter,
            'csv': CSVExporter,
            'xml': XMLExporter}[datatype]
        self.exporter = klass(data, columns, basename)

    def __call__(self):
        return self.exporter()
