"""Reseñas de tiendas."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from features.accounts.infrastructure.permissions import IsCustomer
from features.stores.infrastructure.models import StoreReview


class StoreReviewSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    store_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
    customer_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class CreateStoreReviewSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
    order_id = serializers.IntegerField(required=False, allow_null=True)


@extend_schema_view(
    get=extend_schema(responses={200: StoreReviewSerializer(many=True)}),
    post=extend_schema(request=CreateStoreReviewSerializer, responses={201: StoreReviewSerializer}),
)
class StoreReviewListView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsCustomer()]
        return [AllowAny()]

    def get(self, request, store_id: int):
        reviews = StoreReview.objects.filter(store_id=store_id).select_related("customer")[:50]
        return Response([self._serialize(r) for r in reviews])

    def post(self, request, store_id: int):
        serializer = CreateStoreReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = StoreReview.objects.create(
            store_id=store_id,
            customer_id=request.user.id,
            order_id=serializer.validated_data.get("order_id"),
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(self._serialize(review), status=status.HTTP_201_CREATED)

    @staticmethod
    def _serialize(review: StoreReview) -> dict:
        name = review.customer.username
        profile = getattr(review.customer, "customer_profile", None)
        if profile is not None:
            name = profile.display_full_name()
        return {
            "id": review.id,
            "store_id": review.store_id,
            "rating": review.rating,
            "comment": review.comment,
            "customer_name": name,
            "created_at": review.created_at,
        }
