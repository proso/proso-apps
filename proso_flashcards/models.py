from django.conf import settings
from django.db import models
from proso_models.models import Item, Answer, get_environment
from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver


class Term(models.Model):
    identifier = models.SlugField()
    item = models.ForeignKey(Item, null=True, default=None, related_name="flashcard_terms")

    lang = models.CharField(max_length=2)
    name = models.TextField()
    type = models.CharField(max_length=50, null=True, blank=True)

    def to_json(self, nested=False):
        json = {
            "id": self.pk,
            "item_id": self.item_id,
            "object_type": "fc_term",
            "lang": self.lang,
            "name": self.name,
            "type": self.type,
        }
        if not nested:
            json["parents"] = [parent.to_json(nested=True) for parent in self.parents.all()]
        return json

    def __unicode__(self):
        return "{0.lang} - {0.name}".format(self)


class Context(models.Model):
    identifier = models.SlugField()
    item = models.ForeignKey(Item, null=True, default=None, related_name="flashcard_contexts")

    lang = models.CharField(max_length=2)
    name = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)

    def to_json(self, nested=False):
        return {
            "id": self.pk,
            "item_id": self.item_id,
            "object_type": "fc_context",
            "lang": self.lang,
            "name": self.name,
            "content": self.content,
        }

    def __unicode__(self):
        return "{0.lang} - {0.name}".format(self)


class Flashcard(models.Model):
    identifier = models.SlugField()
    item = models.ForeignKey(Item, null=True, default=None, related_name="flashcards")

    lang = models.CharField(max_length=2)
    term = models.ForeignKey(Term, related_name="flashcards")
    context = models.ForeignKey(Context, related_name="flashcards")
    description = models.TextField(null=True)

    def to_json(self, nested=False):
        return {
            "id": self.pk,
            "item_id": self.item_id,
            "object_type": "fc_flashcard",
            "lang": self.lang,
            "term": self.term.to_json(nested=True),
            "context": self.context.to_json(nested=True),
            "description": self.description
        }

    def __unicode__(self):
        return "{0.term} - {0.context}".format(self)


class Category(models.Model):
    identifier = models.SlugField()
    item = models.ForeignKey(Item, null=True, default=None, related_name="flashcard_categories")

    lang = models.CharField(max_length=2)
    name = models.TextField()
    type = models.CharField(max_length=50, null=True, blank=True)
    subcategories = models.ManyToManyField("self", related_name="parents", symmetrical=False)
    terms = models.ManyToManyField(Term, related_name="parents")

    def to_json(self, nested=False):
        return {
            "id": self.pk,
            "item_id": self.item_id,
            "object_type": "fc_category",
            "lang": self.lang,
            "name": self.name,
            "type": self.type,
        }

    def __unicode__(self):
        return "{0.lang} - {0.name}".format(self)


class FlashcardAnswer(Answer):
    FROM_TERM = "t2d"
    FROM_DESCRIPTION = "d2t"
    DIRECTIONS = (
        (FROM_TERM, "From term to description"),
        (FROM_DESCRIPTION, "From description to term"),
    )

    direction = models.CharField(choices=DIRECTIONS, max_length=3)
    options = models.ManyToManyField(Term, related_name="answers_with_this_as_option")
    meta = models.TextField(null=True, blank=True)

    def to_json(self, nested=False):
        json = Answer.to_json(self)
        json['direction'] = self.direction
        json['meta'] = self.meta
        json['object_type'] = "fc_answer"
        if not nested:
            json["options"] = [term.to_json(nested=True) for term in self.options.all()]
        return json


@receiver(pre_save, sender=Term)
@receiver(pre_save, sender=Context)
@receiver(pre_save, sender=Flashcard)
@receiver(pre_save, sender=Category)
def create_items(sender, instance, **kwargs):
    if instance.item_id is None and instance.item is None:
        item = Item()
        item.save()
        instance.item = item


PROSO_MODELS_TO_EXPORT = [Category, Flashcard, FlashcardAnswer,
                          settings.PROSO_FLASHCARDS.get("context_extension", Context),
                          settings.PROSO_FLASHCARDS.get("term_extension", Term)]


@receiver(m2m_changed, sender=Category.terms.through)
@receiver(m2m_changed, sender=Category.subcategories.through)
def update_parents(sender, instance, action, reverse, model, pk_set, **kwargs):

    environment = get_environment()
    parent_items = []
    child_items = []

    if action == "pre_clear":
        if not reverse:
            parent_items = [instance.item_id]
            children = instance.terms if model == Term else instance.subcategories
            child_items = children.all().values_list("item_id", flat=True)
        else:
            parent_items = instance.parents.all().values_list("item_id", flat=True)
            child_items = [instance.item_id]

    if action == "post_add" or action == "post_remove":
        if not reverse:
            parent_items = [instance.item_id]
            child_items = model.objects.filter(pk__in=pk_set).values_list("item_id", flat=True)
        else:
            parent_items = Category.objects.filter(pk__in=pk_set).values_list("item_id", flat=True)
            child_items = [instance.item_id]

    if action == "post_add":
        for parent_item in parent_items:
            for child_item in child_items:
                environment.write("child", 1, item=parent_item, item_secondary=child_item, symmetric=False)
                environment.write("parent", 1, item=child_item, item_secondary=parent_item, symmetric=False)
        return

    if action == "post_remove" or "pre_clear":
        for parent_item in parent_items:
            for child_item in child_items:
                 environment.delete("child", item=parent_item, item_secondary=child_item)
                 environment.delete("parent", item=child_item, item_secondary=parent_item)
        return
