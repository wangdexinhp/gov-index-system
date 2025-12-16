from django.contrib import admin

from apps.coredata.models.geography import Province, City
from apps.coredata.models.indicator import Indicator
from apps.coredata.models.rank import CityRank


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "province")
    list_filter = ("province",)
    search_fields = ("code", "name")


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("name_zh", "name_en", "input_form", "indicator_type")
    list_filter = ("input_form", "indicator_type")
    search_fields = ("name_zh", "name_en")


@admin.register(CityRank)
class CityRankValueAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "get_province",
        "city",
        "indicator_name_zh",
        "indicator_name_en",
        "value",
    )

    list_filter = (
        "year",
        "city__province",          # 通过外键跨表过滤省份
        "city",
        "indicator__indicator_type",
    )

    search_fields = (
        "indicator__name_zh",
        "indicator__name_en",
        "city__name",
        "city__province__name",
    )

    autocomplete_fields = ("city", "indicator")
    list_per_page = 50

    fieldsets = (
        (
            "基本信息",
            {
                "fields": (
                    "year",
                    "city",
                    "indicator",
                    "value",
                )
            },
        ),
    )

    def indicator_name_zh(self, obj):
        return obj.indicator.name_zh

    indicator_name_zh.short_description = "指标名称（中文）"

    def indicator_name_en(self, obj):
        return obj.indicator.name_en

    indicator_name_en.short_description = "指标名称（英文）"

    def get_province(self, obj):
        return obj.city.province if obj.city else None

    get_province.short_description = "省份"
    get_province.admin_order_field = "city__province"
