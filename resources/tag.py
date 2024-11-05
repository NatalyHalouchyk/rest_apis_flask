import sys
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError

from db import db
from schemas import TagSchema, ItemAndTagSchema
from models import TagModel, StoreModel, ItemModel

blp = Blueprint("tags", __name__, description="Operations on tags")

@blp.route("/stores/<int:store_id>/tags")
class TagInStore(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)

        return store.tags.all()
    
    @jwt_required()
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        if TagModel.query.filter(TagModel.store_id == tag_data["store_id"], TagModel.name == tag_data["name"]).first():
            abort(400, message="A tag with that name already exists in that store.")

        new_tag = TagModel(**tag_data)

        try:
            db.session.add(new_tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        return new_tag
    
@blp.route("/items/<int:item_id>/tags/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @jwt_required()
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the tag.")

        return tag
    
    @jwt_required()
    @blp.response(200, ItemAndTagSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.remove(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while deleting the tag.")

        return {"message": "Tag removed from item.", "item": item, "tag":tag }

    

@blp.route("/tags/<int:tag_id>")
class Tag(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        return TagModel.query.get_or_404(tag_id)
    
    @jwt_required(fresh=True)
    @blp.response(202, description="Deletes a tag if no item is tagged with it.")
    @blp.alt_response(404, description="Tag not found")
    @blp.alt_response(400, description="Returned if the tag is assigned to one or more items. In this case, tag is not deleted.")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
        else:
            abort(400, message="Could not delete tag. Make sure tag is not associated with any items, then try again.")

        return {"message": "Tag deleted."}

@blp.route("/tags")
class TagList(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self):
        return TagModel.query.all()