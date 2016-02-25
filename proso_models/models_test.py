from .models import Item, ItemRelation
from django.core.management import call_command
from proso_flashcards.models import Flashcard, Category
from testproject.testapp.models import ExtendedContext, ExtendedTerm
import django.test as test


class ItemManagerGraphTest(test.TestCase):

    '''
        1
       / \
      2   3   4
     / \ / \ /
    5   6   7
    '''
    GRAPH = {
        1: [2, 3],
        2: [5, 6],
        3: [6, 7],
        4: [7],
        5: [],
        6: [],
        7: [],
    }

    @classmethod
    def setUpClass(cls):
        super(ItemManagerGraphTest, cls).setUpClass()
        for item_id in ItemManagerGraphTest.GRAPH.keys():
            item = Item.objects.create(id=item_id)
        for item_id, children in ItemManagerGraphTest.GRAPH.items():
            item = Item.objects.get(id=item_id)
            for child in children:
                ItemRelation.objects.create(parent=item, child=Item.objects.get(id=child))
            item.save()

    def test_parents_graph(self):
        self.assertEqual(Item.objects.get_parents_graph([4]), {None: [4]})
        self.assertEqual(
            Item.objects.get_parents_graph([6]),
            {None: [6], 6: [2, 3], 2: [1], 3: [1]}
        )
        self.assertEqual(
            Item.objects.get_parents_graph([6, 7]),
            {None: [6, 7], 6: [2, 3], 7: [3, 4], 2: [1], 3: [1]}
        )

    def test_children_graph(self):
        self.assertEqual(Item.objects.get_children_graph([7]), {None: [7]})
        self.assertEqual(
            Item.objects.get_children_graph([1]),
            {None: [1], 1: [2, 3], 2: [5, 6], 3: [6, 7]}
        )
        self.assertEqual(
            Item.objects.get_children_graph([2, 4]),
            {None: [2, 4], 2: [5, 6], 4: [7]}
        )

    def test_get_leaves(self):
        self.assertEqual(Item.objects.get_leaves([4]), {7})
        self.assertEqual(Item.objects.get_leaves([2, 3]), {5, 6, 7})


class TestItemManager(test.TestCase):

    fixtures = [
        'test_common_data.yaml',
        'test_models_data.yaml',
        'test_flashcards_data.yaml',
        'test_testapp_data.yaml'
    ]

    def setUp(self):
        self._categories = dict([((c.identifier, c.lang), c) for c in Category.objects.all()])
        self._contexts = dict([((c.identifier, c.lang), c) for c in ExtendedContext.objects.all()])
        self._terms = dict([((t.identifier, t.lang), t) for t in ExtendedTerm.objects.prefetch_related('parents').all()])
        self._flashcards = dict([((f.identifier, f.lang), f) for f in Flashcard.objects.select_related('term', 'context').all()])
        call_command('find_item_types')
        call_command('fill_item_types')

    def test_translate_item_ids(self, language='cs'):
        all_objects = {}
        for objects in [self._flashcards, self._categories, self._terms]:
            for (_, lang), o in objects.items():
                if lang != language:
                    continue
                all_objects[o.item_id] = o
        not_nested_item = list(self._flashcards.values())[0].item_id
        json_objects = Item.objects.translate_item_ids(list(all_objects.keys()), 'cs', is_nested=lambda i: i != not_nested_item)
        self.assertEqual(len(json_objects), len(all_objects))
        for item_id, json_object in json_objects.items():
            self.assertEqual(json_object, all_objects[item_id].to_json(nested=not_nested_item!=item_id))

    def test_translate_identifiers(self, language='cs'):
        self.assertEqual(
            Item.objects.translate_identifiers(['flashcard/africa-bw', 'category/world'], 'cs'),
            {'category/world': 1, 'flashcard/africa-bw': 74}
        )
