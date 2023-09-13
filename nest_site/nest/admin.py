from django.contrib import admin
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe

from .models import Experiment, Experimenter, Round, \
    Session, Stimulus, StimulusGroup, StimulusVoteGroup, Subject, Vote, VoteRegister


# =================
# ==== Inline =====
# =================


class SessionInline(admin.StackedInline):
    model = Session
    extra = 0
    fields = ['experiment', 'subject',
              'get_edit_link',
              # 'is_active',
              ]
    readonly_fields = ['experiment',
                       # 'subject',
                       'get_edit_link',
                       # 'is_active',
                       ]

    def get_edit_link(self, obj=None):
        if obj.pk:
            url = reverse('admin:%s_%s_change' % (obj._meta.app_label,
                                                  obj._meta.model_name),
                          args=[force_str(obj.pk)])
            return mark_safe("""<a href="{url}">{text}</a>""".format(
                url=url,
                text="Edit this %s separately" % obj._meta.verbose_name,
            ))
        return "(save and continue editing to create a link)"

    get_edit_link.short_description = "Edit link"


class RoundInline(admin.StackedInline):
    model = Round
    extra = 0
    fields = ['session',
              'get_edit_link',
              'response_sec',
              # 'is_active',
              ]
    readonly_fields = ['session',
                       'get_edit_link',
                       'response_sec',
                       # 'is_active',
                       ]

    def get_edit_link(self, obj=None):
        if obj.pk:
            url = reverse('admin:%s_%s_change' % (obj._meta.app_label,
                                                  obj._meta.model_name),
                          args=[force_str(obj.pk)])
            return mark_safe("""<a href="{url}">{text}</a>""".format(
                url=url,
                text="Edit this %s separately" % obj._meta.verbose_name,
            ))
        return "(save and continue editing to create a link)"

    get_edit_link.short_description = "Edit link"


class VoteInline(admin.StackedInline):
    model = Vote
    extra = 0
    fields = ['score', 'round',
              'get_edit_link',
              # 'is_active',
              ]
    readonly_fields = ['score', 'round',
                       'get_edit_link',
                       # 'is_active',
                       ]

    def get_edit_link(self, obj=None):
        if obj.pk:
            url = reverse('admin:%s_%s_change' % (obj._meta.app_label,
                                                  'vote'),
                          args=[force_str(obj.pk)])
            return mark_safe("""<a href="{url}">{text}</a>""".format(
                url=url,
                text="Edit this %s separately" % 'vote',
            ))
        return "(save and continue editing to create a link)"

    get_edit_link.short_description = "Edit link"


# ====================
# ==== ModelAdmin ====
# ====================


class ExperimentAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['title', 'id',
                                         'experimenter_list',
                                         'description']}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
        ('Tools', {'fields': ['download_dataset']}),
    ]
    readonly_fields = ['id',
                       'create_date',
                       # 'is_active',
                       'download_dataset',
                       'experimenter_list',
                       ]
    inlines = [SessionInline]
    list_display = ('title', 'id', 'experimenter_list', 'description', 'create_date',
                    'download_dataset')
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]
    search_fields = ['title', 'description']

    def download_dataset(self, obj):
        e = Experiment.objects.get(id=obj.id)
        return mark_safe(
            """<a href="{sureal}">S1</a> | <a href="{sureal_alt}">S2</a> | <a href="{nest}">NEST</a> | <a href="{nest_csv}">CSV</a>""".
            format(
                sureal=reverse('admin:download_sureal', args=[force_str(e.pk)]),
                sureal_alt=reverse('admin:download_sureal_alt', args=[force_str(e.pk)]),
                nest=reverse('admin:download_nest', args=[force_str(e.pk)]),
                nest_csv=reverse('admin:download_nest_csv', args=[force_str(e.pk)])))

    download_dataset.short_description = 'Dataset'

    def experimenter_list(self, obj):
        er_html_list = list()
        for er in obj.experimenters.all():
            text = str(er)
            url = reverse('admin:%s_%s_change' % (er._meta.app_label,
                                                  er._meta.model_name),
                          args=[force_str(er.pk)])
            er_html_list.append("""<a href="{url}">{text}</a>""".format(
                url=url, text=text))
        return mark_safe("<br>".join(er_html_list))

    experimenter_list.short_description = 'Experimenters'


class SessionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['__str__', 'id', 'experiment', 'subject']}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
    ]
    readonly_fields = ['__str__', 'id',
                       'create_date',
                       'experiment',
                       # 'subject',
                       # 'is_active',
                       ]
    inlines = [RoundInline]
    list_display = ('__str__', 'id',
                    'experiment',
                    'subject',
                    # 'is_active',
                    )
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]


class RoundAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['__str__', 'id',
                                         'round_id',
                                         'session',
                                         'stimulusgroup',
                                         'response_sec',
                                         ]}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
    ]
    readonly_fields = ['__str__', 'id',
                       'round_id',
                       'create_date',
                       'session',
                       'stimulusgroup',
                       'response_sec',
                       # 'is_active',
                       ]
    inlines = [VoteInline]
    list_display = ('__str__', 'id',
                    'round_id',
                    'session',
                    'stimulusgroup',
                    'response_sec',
                    # 'is_active',
                    )
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]


class VoteAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['__str__', 'id',
                                         'score', 'round', 'stimulusvotegroup']}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
    ]
    readonly_fields = ['__str__', 'id',
                       'create_date',
                       # 'is_active',
                       'round', 'stimulusvotegroup']
    list_display = ('__str__', 'id',
                    'score',
                    'round',
                    # 'is_active',
                    )
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]


class StimulusAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['__str__', 'id',
                                         'stimulus_id',
                                         'experiment',
                                         'content',
                                         'condition']}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
    ]
    readonly_fields = ['__str__', 'id',
                       'create_date',
                       'stimulus_id',
                       'experiment',
                       'content',
                       'condition',
                       # 'is_active',
                       ]
    list_display = ('__str__', 'id',
                    'stimulus_id',
                    'experiment',
                    'content', 'condition',
                    # 'is_active',
                    )
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]


class StimulusGroupAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['__str__', 'id',
                                         'stimulusgroup_id',
                                         'experiment',
                                         'stimuli']}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
    ]
    readonly_fields = ['create_date',
                       '__str__', 'id',
                       'stimulusgroup_id',
                       'experiment',
                       'stimuli',
                       # 'is_active',
                       ]
    list_display = ('__str__',
                    'id',
                    'stimulusgroup_id',
                    'experiment',
                    'stimuli',
                    # 'is_active',
                    )
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]


class StimulusVoteGroupAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['__str__', 'id',
                                         'stimulus_list',
                                         'stimulusgroup',
                                         'stimulusvotegroup_id',
                                         'experiment',
                                         ]}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
    ]
    readonly_fields = ['create_date',
                       'stimulus_list',
                       'stimulusgroup',
                       'stimulusvotegroup_id',
                       'experiment',
                       '__str__', 'id',
                       # 'is_active',
                       ]
    list_display = ('__str__', 'id', 'stimulus_list', 'stimulusgroup',
                    'stimulusvotegroup_id',
                    'experiment',
                    # 'is_active',
                    )
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]

    def stimulus_list(self, obj):
        stim_html_list = list()
        vrs = VoteRegister.objects.filter(stimulusvotegroup=obj)
        for vr in vrs:
            stimulus_order = vr.stimulus_order
            s = vr.stimulus
            text = str(s) + f' [order {stimulus_order}]'
            url = reverse('admin:%s_%s_change' % (s._meta.app_label,
                                                  s._meta.model_name),
                          args=[force_str(s.pk)])
            stim_html_list.append("""<a href="{url}">{text}</a>""".format(
                url=url, text=text))

        return mark_safe("<br>".join(stim_html_list))

    stimulus_list.short_description = 'Stimulus List'


class SubjectAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['__str__', 'id',
                                         'name', 'user']}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
    ]
    readonly_fields = ['__str__', 'id',
                       'create_date',
                       'name', 'user',
                       # 'is_active',
                       ]
    inlines = [SessionInline]
    list_display = ('__str__', 'id',
                    'name', 'user',
                    # 'is_active',
                    )
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]
    search_fields = ['name']


class ExperimenterAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['__str__', 'id',
                                         'name', 'user']}),
        ('Date information', {'fields': ['create_date',
                                         # 'is_active',
                                         # 'deactivate_date',
                                         ]}),
    ]
    readonly_fields = ['__str__', 'id',
                       'create_date',
                       'name', 'user',
                       # 'is_active',
                       ]
    list_display = ('__str__', 'id',
                    'name', 'user',
                    # 'is_active',
                    )
    list_filter = ['create_date',
                   # 'deactivate_date',
                   ]
    search_fields = ['name']


# ==================
# ==== register ====
# ==================


admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Stimulus, StimulusAdmin)
admin.site.register(StimulusGroup, StimulusGroupAdmin)
admin.site.register(StimulusVoteGroup, StimulusVoteGroupAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Experimenter, ExperimenterAdmin)
