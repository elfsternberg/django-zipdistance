from django.db import models
from django.db.models import Aggregate
from django.db.models.sql.aggregates import Aggregate as AggregateImpl

class DistanceFromImpl(AggregateImpl): 
    sql_function = ''
    is_computed = True
    is_ordinal = True

    sql_template = ('3959 * acos( cos( radians(%(t_lat)f) ) * cos( radians( latitude ) ) * '
                    'cos( radians( longitude ) - radians(%(t_lon)f) ) + sin( radians(%(t_lat)f) ) * '
                    'sin( radians( latitude ) ) )')

    def __init__(self, col, target, **extra): 
        self.col = col
        self.target = target
        self.extra = extra 

    def _default_alias(self): 
        return '%s__%s' % (str(self.target), self.__class__.__name__.lower()) 

    default_alias = property(_default_alias) 

    def add_to_query(self, query, alias, col, source, is_summary): 
        super(DistanceFrom, self).__init__(col, source, is_summary, **self.extra) 
        query.aggregate_select[alias] = self

    def as_sql(self, qn, connection):
        "Return the aggregate, rendered as SQL."

        return self.sql_template % { 't_lon': self.target.longitude,
                                     't_lat': self.target.latitude }


        
class DistanceFrom(Aggregate):
    name="DistanceFromImpl"

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = DistanceFromImpl(col, source=source, is_summary=is_summary, **self.extra)
        query.aggregates[alias] = aggregate
        


class ZipDistanceManager(models.Manager):

    def distance_from(self, target, limit = 0):
        qs = self.annotate(distance = DistanceFrom('zipcode', target = target))
        if bool(limit):
            qs = qs.filter(distance__lte = float(limit))
        qs = qs.order_by('distance')
        return qs



class ZipDistance(models.Model):
    state = models.CharField(max_length = 2)
    zipcode = models.CharField(max_length = 5, unique = True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = ZipDistanceManager()

    class Meta:
        ordering = ['zipcode']

    def __unicode__(self):
        return '%s:%s' % (self.state, self.zipcode)

    def distance_between(self, other):
        return self.__class__.objects.distance_from(self).get(zipcode = other.zipcode).distance

    
        
