from typing import Text, List, Any, Dict
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import AllSlotsReset, SlotSet
import random
from thefuzz import process
from thefuzz import fuzz
import json
import re


def remove_char(input_string):
    pattern = "[^a-zA-Z0-9 ]"
    return re.sub(pattern, " ", input_string)


with open("./actions/filters.json", "r") as file:
    resp_json = json.load(file)

with open("./actions/videos.json", "r") as file:
    videos = json.load(file)


def colls():
    collection_names = []
    collection_handles = []
    for collection in resp_json["data"]["collections"]["nodes"]:
        title = collection["title"]
        title = remove_char(title)
        handle = collection["handle"]
        collection_names.append(title)
        collection_handles.append({title: [handle]})

    collection_names.append("catalogue")
    collection_names.append("all")
    collection_handles.append({"catalogue": ["all"]})
    collection_handles.append({"all": ["all"]})
    coll_dict = {"collection": collection_names}
    return collection_names, collection_handles, coll_dict


def pages():
    page_list = []
    page_list_handle = []
    for page in resp_json["data"]["pages"]["nodes"]:
        title = page["title"]
        # if (is_alpha(title) == False):
        title = remove_char(title)

        handle = page["handle"]
        # if (is_alpha(handle) == False):

        page_list.append(title)
        page_list_handle.append({page["title"]: [handle]})

    page_list.append("back")
    page_list.append("home")
    page_list_handle.append({"back": ["back"]})
    page_list_handle.append({"home": ["home"]})
    page_dict = {"page": page_list}
    return page_list, page_list_handle, page_dict


def options():
    temp_dict = {}
    for products in resp_json["data"]["collections"]["nodes"]:
        filtered_products = [
            product
            for product in products["products"]["filters"]
            if product.get("type") == "LIST"
        ]
        for product in filtered_products:
            for value in product["values"]:
                val = value["label"]
                val = remove_char(val)
                name = product["id"].split(".")[-1]
                name = remove_char(name)
                temp_dict.setdefault(name, []).append(val)

    filter_dict = {}

    for key, values in temp_dict.items():
        unique_values = list(dict.fromkeys(values))
        filter_dict[key] = unique_values

    filter_names = list(filter_dict.keys())

    return filter_names, filter_dict


page_list, page_list_handle, page_dict = pages()
coll_list, coll_list_handle, coll_dict = colls()
option_names, option_dict = options()
option_dict["page"] = page_dict["page"]
option_dict["collection"] = coll_dict["collection"]


def transformed_options():
    filter_names, filter_dict = options()

    page_list, page_list_handle, page_dict = pages()

    collection_names, collection_handles, coll_dict = colls()
    transformed_dict = {}
    for key, values in filter_dict.items():
        transformed_values = []

        for value in values:
            value_dict = {value: [v for v in values if v.lower() == value.lower()]}
            transformed_values.append(value_dict)

        transformed_dict[key] = transformed_values
    transformed_dict["collection"] = collection_handles
    transformed_dict["page"] = page_list_handle

    return transformed_dict


transform_option_dict = transformed_options()
possible_filters = option_names + ["price"]


# Different video links and their corresponding texts
def switch_case_filter(filter):
    switch_dict = {
        None: [
            {
                "video_link": "filter-complete-1.mp4",
                "text": "Excellent pick! We've got a wide array that might pique your interest.",
            },
            {
                "video_link": "filter-complete-2.mp4",
                "text": "Impressive choice! Our curated selection is sure to please.",
            },
            {
                "video_link": "filter-complete-3.mp4",
                "text": "Superb choice! We've got a diverse range for you to explore.",
            },
            {
                "video_link": "filter-complete-4.mp4",
                "text": "Terrific pick! Our collection is tailored to your tastes.",
            },
            {
                "video_link": "filter-complete-5.mp4",
                "text": "Excellent decision! We have a range that suits your preferences.",
            },
        ],
        "color": [
            {
                "video_link": "color-4.mp4",
                "text": "Here is the selection that you asked for. Did you have a specific colour in mind?",
            },
            {
                "video_link": "color-5.mp4",
                "text": "Here's the requested products! Do you have a preferred colour in mind?",
            },
            {
                "video_link": "color-6.mp4",
                "text": "I've located the items you asked for. Is there a particular colour you're aiming for?",
            },
            {
                "video_link": "color-7.mp4",
                "text": "I've found these for you, what do you think? Did you have a specific colour in mind?",
            },
            {
                "video_link": "color-8.mp4",
                "text": "I've compiled this selection for you. What are your thoughts? Is there a particular colour that you're looking for?",
            },
        ],
        "size": [
            {
                "video_link": "size-4.mp4",
                "text": "Here's the items you were after. What do you think? Are you looking for a specific size?",
            },
            {
                "video_link": "size-5.mp4",
                "text": "Amazing. Here are the relevant products that you requested. Do you want me to look for a certain size?",
            },
        ],
        "tag": [
            {
                "video_link": "tag-1.mp4",
                "text": "Are you leaning toward a specific style, such as comfortable or casual?",
            },
            {
                "video_link": "tag-2.mp4",
                "text": "Do you have a particular style preference, like comfortable or casual?",
            },
            {
                "video_link": "tag-3.mp4",
                "text": "Is there a specific style on your mind, such as comfortable or casual?",
            },
        ],
        "lessthan": [
            {
                "video_link": "budget-1.mp4",
                "text": "How much are you looking to spend?",
            },
            {
                "video_link": "filter-4.mp4",
                "text": "Here is our selection within that range",
            },
        ],
        "morethan": [
            {
                "video_link": "filter-3.mp4",
                "text": "Great choice! Selecting your preference right now",
            },
            {
                "video_link": "filter-4.mp4",
                "text": "Here is our selection within that range",
            },
        ],
        "page": [{"video_link": "filter-3.mp4", "text": "Here you go"}],
    }

    return switch_dict.get(
        filter,
        [
            {
                "video_link": "filter-left-1.mp4",
                "text": "Fantastic selection! Is there anything specific you're interested in exploring further?",
            },
            {
                "video_link": "filter-left-2.mp4",
                "text": "Wonderful decision! Are there more aspects you'd like to discover in our offerings?",
            },
            {
                "video_link": "filter-left-3.mp4",
                "text": "Outstanding selection! Any other particular elements that you'd like to focus on?",
            },
            {
                "video_link": "filter-left-4.mp4",
                "text": "Great selection! Have you thought about refining your search for a more tailored experience?",
            },
            {
                "video_link": "filter-left-5.mp4",
                "text": "Fantastic choice! Is there something else you'd like to uncover in our collection?",
            },
        ],
    )


# Transferring the entities we get into the State Dict
def entities_2_json(state, entities):
    new_events = []
    for ent in entities:
        if ent["entity"] == "price":
            state[ent["role"]] = ent["value"]

        elif state[ent["entity"]] and (ent["value"] not in state[ent["entity"]]):
            state[ent["entity"]].append(ent["value"])

        else:
            state[ent["entity"]] = [ent["value"]]

    for key, value in state.items():
        new_events.append(SlotSet(key, value))

    return new_events, state


# Making all States None
def filter_refresh(state):
    for key in state:
        state[key] = None

    return state


# Making all filters None
def filter_remove_all(state):
    for key in state:
        if key == "collection":
            continue
        state[key] = None

    new_events = []
    for key, value in state.items():
        new_events.append(SlotSet(key, value))

    return new_events, state


# Making single filters None
def filter_remove_single(filter_slot, state):
    if filter_slot == "price":
        state["lessthan"] = None
        state["morethan"] = None
    else:
        state[filter_slot] = None

    new_events = []
    for key, value in state.items():
        new_events.append(SlotSet(key, value))

    new_events.append(SlotSet("filter", None))
    return new_events, state


# Getting video and text using random
def video_generate(filter_left):
    utter = random.choice(switch_case_filter(filter_left))
    text = utter["text"]
    video_link = utter["video_link"]

    return video_link, text


# Changing the format of filters for the frontend
def value_correction(state):
    final_dict = {}
    final_dict["price"] = {"lessthan": state["lessthan"], "morethan": state["morethan"]}
    for slot_key, slot_values in state.items():
        if slot_values and slot_key != "lessthan" and slot_key != "morethan":
            slots = []
            for single_slot in slot_values:
                closest_match = process.extractOne(
                    single_slot,
                    option_dict[slot_key],
                    scorer=fuzz.ratio,
                    score_cutoff=70,
                )

                if closest_match:
                    verified_items = []
                    for item in transform_option_dict[slot_key]:
                        if closest_match[0] in item.keys():
                            verified_items.append(item[closest_match[0]])
                    slots.extend(
                        v.replace(" ", "+") for v_list in verified_items for v in v_list
                    )
                    final_dict[slot_key] = slots

        else:
            final_dict[slot_key] = slot_values

    del final_dict["lessthan"]
    del final_dict["morethan"]
    return final_dict


state_dict = {key: None for key, value in option_dict.items()}
state_dict["lessthan"] = None
state_dict["morethan"] = None


class ActionSearch(Action):
    def name(self) -> Text:
        return "action_search"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        global state_dict

        print("current state", state_dict)

        entities = tracker.latest_message["entities"]

        entities = [entry for entry in entities if entry["entity"] != "filter"]

        current_collection = tracker.get_slot("collection")

        # Refresh State Dict, if new collection
        if state_dict["collection"] != current_collection:
            state_dict = filter_refresh(state_dict)

        # Place new entities in State Dict and get events
        new_events, state_dict = entities_2_json(state_dict, entities)

        print("new state", state_dict)

        # Format dict for Frontend
        final_dict = value_correction(state_dict)

        # Getting the name of the first filter that is None
        filter_left = next(
            (
                key
                for key, value in state_dict.items()
                if value is None and key != "page"
            ),
            None,
        )

        if final_dict["page"]:
            state_dict = filter_refresh(state_dict)
            filter_video, filter_text = video_generate("page")
            new_events, state_dict = entities_2_json(state_dict, entities)
            final_dict = value_correction(state_dict)
            final_dict["action_name"] = "navigate"
            final_dict["video_link"] = filter_video
            dispatcher.utter_message(filter_text)
            dispatcher.utter_message(json_message=final_dict)
            return [AllSlotsReset()]

        # Generate Video and Text
        filter_video, filter_text = video_generate(filter_left)
        final_dict["video_link"] = filter_video
        final_dict["action_name"] = "filter"
        dispatcher.utter_message(filter_text)
        dispatcher.utter_message(json_message=final_dict)
        return new_events


class ActionRemoveFilter(Action):
    def name(self) -> Text:
        return "action_remove_filter"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        global state_dict

        filter_slot = tracker.get_slot("filter")
        print(filter_slot)

        if filter_slot is None:
            cust = {"action_name": "remove_filters"}
            dispatcher.utter_message("Removing filters")
            dispatcher.utter_message(json_message=cust)
            events, state_dict = filter_remove_all(state_dict)
            return events

        elif filter_slot in possible_filters:
            # dispatcher.utter_message(json_message=cust)
            events, state_dict = filter_remove_single(filter_slot, state_dict)
            final_dict = value_correction(state_dict)
            final_dict["action_name"] = "remove_filter_single"
            final_dict["video_link"] = ""
            dispatcher.utter_message("Removing filters")
            dispatcher.utter_message(json_message=final_dict)

            return events
        return []


class ActionSelection(Action):
    def name(self) -> Text:
        return "action_selection"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        global state_dict

        final_dict = {}
        result_list = [
            value
            for dictionary in coll_list_handle
            for value_list in dictionary.values()
            for value in value_list
        ]

        filter_slot = tracker.get_slot("filter")
        collection_slot = tracker.get_slot("collection")

        filter_match = process.extractOne(
            filter_slot, option_names, scorer=fuzz.ratio, score_cutoff=70
        )
        if collection_slot is not None:
            collection_slot = collection_slot[0]
            collection_match = process.extractOne(
                collection_slot, result_list, scorer=fuzz.ratio, score_cutoff=70
            )

        try:
            if filter_match is not None and collection_match is None:
                out = videos["main"][filter_match[0]]
                text = out["text"]
                video_id = out["video_id"]
                final_dict["action_name"] = "no-action"
                final_dict["video_link"] = None
                final_dict["video_id"] = video_id
                dispatcher.utter_message(text)
                dispatcher.utter_message(json_message=final_dict)

            elif filter_match is not None and collection_match is not None:
                out = videos[collection_match[0]][filter_match[0]]
                text = out["text"]
                video_id = out["video_id"]
                final_dict["action_name"] = "no-action"
                final_dict["video_link"] = None
                final_dict["video_id"] = video_id
                dispatcher.utter_message(text)
                dispatcher.utter_message(json_message=final_dict)
        except:
            dispatcher.utter_message("We don't have that filter in this collection")
            final_dict["action_name"] = "no-action"
            final_dict["video_link"] = "okay-1.mp4"
            dispatcher.utter_message(json_message=final_dict)

        return [SlotSet("filter", None)]


class ActionInquireStore(Action):
    def name(self) -> Text:
        return "action_inquire_store"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        global state_dict

        final_dict = {}
        print("inquire")
        final_dict["action_name"] = "no-action"
        final_dict["video_link"] = None
        final_dict["video_id"] = 'intro'
        dispatcher.utter_message('Intro Text')
        dispatcher.utter_message(json_message=final_dict)
        return []


class ActionSlotter(Action):
    def name(self) -> Text:
        return "action_slotter"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        global state_dict

        print("slotter current state", state_dict)
        entities = tracker.latest_message["entities"]
        current_collection = tracker.get_slot("collection")
        if state_dict.get("collection") != current_collection:
            state_dict = filter_refresh(state_dict)
        new_events, state_dict = entities_2_json(state_dict, entities)
        print("slotter new state", state_dict)

        return new_events
