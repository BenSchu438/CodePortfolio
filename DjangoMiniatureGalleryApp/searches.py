from django.conf import settings
from django.db.models import Sum
from .models import *

PUNCTIUATION_STRIP = " ,./<>?;':\"\\[]}{|=-`~_+)(*&^%$#@!"
MAX_STRING = 128

def get_gallery_context_stats(query_hits):
    '''
    Get a dictionary of stats to be passed in as context to the gallery view.
    '''
    # get baseline stats
    total_batch_count = Batch.objects.count()
    total_model_count = Batch.objects.all().aggregate(Sum('count', default=0))['count__sum']
    
    # calculate query hit stats 
    result_batch_count = len(query_hits)
    results_points = 0
    result_model_count = 0
    for b in query_hits:
        results_points += b.total_points()
        result_model_count += b.count
    
    # calculate ratios
    result_batch_ratio = ( result_batch_count / total_batch_count ) * 100
    result_model_ratio = ( result_model_count / total_model_count ) * 100
    # format to percent string
    result_batch_ratio = f'{result_batch_ratio:.2f}%'
    result_model_ratio = f'{result_model_ratio:.2f}%'

    return {
        'results_points': results_points,
        'total_batch_count' : total_batch_count,
        'total_model_count' : total_model_count,
        'batch_count' : result_batch_count,
        'model_count' : result_model_count,
        'batch_ratio' : result_batch_ratio,
        'model_ratio' : result_model_ratio,
    }



def wide_db_search(search_terms):
    '''
    Get a list of batches, unsorted, that fit the passed in criteria
    '''
    if settings.DEBUG:
        print(search_terms)

    # store results in set. Intersect each continuous set to ensure 'AND' behavior
    output_set = set()
    # cache terms so we can skip repeat queries and print out 'hits' later
    terms = []

    for potential_tag in search_terms:
        # check each case, organized to do fastest checks first
        # TAG, CATEGORY, STAGE, KIT, UNIT_TYPE, UNIT_NAME
        # Majority of logic is contained in their appropriate model classes
        subsearch = set()

        # analyze each test, adding the first success possible

        if tag := Tag.get_tag_via_name(potential_tag):
            if tag.name in terms:
                continue
            terms.append(tag.name)
            subsearch = set( tag.get_tagged_batches() )

        elif category := Category.get_category_via_name(potential_tag):
            if category in terms:
                continue
            terms.append(category)
            subsearch = set( category.get_category_batches() )

        elif stage := Batch.get_stage_via_name(potential_tag):
            if stage in terms:
                continue
            terms.append(stage)
            subsearch = set( Batch.get_batches_of_stage(stage) )

        elif Unit.has_unit_type_of_name(potential_tag):
            if potential_tag in terms:
                continue
            terms.append(potential_tag)
            subsearch = set( Unit.get_batches_of_unit_type(potential_tag) )

        elif Unit.has_units_of_name(potential_tag):
            if potential_tag in terms:
                continue
            terms.append(potential_tag)
            subsearch = set( Unit.get_batches_with_unit_name(potential_tag) )
        
        elif kit := Kit.get_kit_via_name(potential_tag):
            if kit.name in terms:
                continue
            terms.append(kit.name)
            subsearch = set( kit.get_batches_of_kit() )

        # if nothing found in subsearch, move to next keyword
        if len(subsearch) == 0:
            continue
        # If an empty output_set, this was the first hit, so use all subsearch hits
        elif len(output_set) == 0:
            output_set = output_set.union(subsearch)
        # Otherwise, filter hits for 'AND' effect 
        else:
            output_set = output_set.intersection(subsearch)

    # return both hits and terms. Return terms for HTML bonuses
    return list(output_set), terms

def is_valid_search_string(tag_string : str):
    '''
    Returns whether a search string is valid to use in the search query.
    '''
    if tag_string is None:
        return False
    else:
        trimmed_str = tag_string.strip(PUNCTIUATION_STRIP)
        return len(trimmed_str) > 0

def parse_search_string(tag_string : str):
    '''
    parse and format a long search string into a list of usable search terms. Returns empty list if no string found.
    '''
    # if over the limit, truncate it
    if len(tag_string) > MAX_STRING:
        tag_string = tag_string[:MAX_STRING]
    
    # exit early if empty
    if tag_string == '':
        return []
    
    # clean string with uneccesary punctuation at the start/end
    new_list = tag_string.strip(PUNCTIUATION_STRIP)

    # format to be CSV with spaces allowed. Also remove <>'s to minimize any risk of html brackets
    new_list = new_list.replace(" ", ",")
    new_list = new_list.replace("<", ",")
    new_list = new_list.replace(">", ",")
    new_list = new_list.replace("_", " ")

    # split into list
    new_list = new_list.split(",")

    # strip each again just to be safe. 
    results = []
    for idx, item in enumerate(new_list):
        new_list[idx] = item.strip(PUNCTIUATION_STRIP)

        # put in results if not an empty string
        if new_list[idx] != '':
            results.append(new_list[idx])

    return results