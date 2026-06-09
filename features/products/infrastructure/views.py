from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.pagination import paginate_list
from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.products.application.dto import (
    CreateCategoryDTO,
    CreateProductDTO,
    CreateServiceDTO,
    CreateSubcategoryDTO,
    DeactivateProductDTO,
    UpdateCategoryDTO,
    UpdateProductStockDTO,
)
from features.products.domain.entities import ProductType
from features.products.domain.exceptions import (
    CategoryNotFoundError,
    DomainValidationError,
    InvalidCategoryHierarchyError,
    ProductNotFoundError,
    VariantsNotAllowedError,
)
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.products.infrastructure.serializers import (
    CategoryTreeSerializer,
    CreateCategorySerializer,
    CreateProductSerializer,
    CreateServiceSerializer,
    CreateSubcategorySerializer,
    ProductDetailSerializer,
    ProductSerializer,
    UpdateProductSerializer,
    UpdateStockSerializer,
    UpdateCategorySerializer,
)

CategoryResponseSerializer = inline_serializer(
    name="CategoryResponse",
    fields={
        "id": serializers.IntegerField(),
        "name": serializers.CharField(),
        "store_id": serializers.IntegerField(),
        "parent_id": serializers.IntegerField(allow_null=True),
    },
)


def _product_serializer_data(products, repository):
    items = products if isinstance(products, list) else [products]
    primary_urls = repository.primary_image_urls_for_products([item.id for item in items])
    serializer = ProductSerializer(
        products,
        many=isinstance(products, list),
        context={"primary_image_urls": primary_urls},
    )
    return serializer.data


@extend_schema_view(
    get=extend_schema(responses={200: ProductSerializer(many=True)}),
    post=extend_schema(
        request=CreateProductSerializer,
        responses={201: ProductSerializer, 400: DetailErrorSerializer, 403: DetailErrorSerializer},
    ),
)
class StoreProductListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMerchant()]
        return [AllowAny()]

    def get(self, request, store_id: int):
        from features.products.infrastructure.repositories import DjangoProductRepository
        from features.products.infrastructure.serializers import ProductSerializer

        product_type = request.query_params.get("type")
        category_id = request.query_params.get("category")
        subcategory_id = request.query_params.get("subcategory")
        search = request.query_params.get("search")

        parsed_type = ProductType(product_type) if product_type else None
        parsed_category = int(category_id) if category_id else None
        parsed_subcategory = int(subcategory_id) if subcategory_id else None

        repository = DjangoProductRepository()
        products = repository.list_by_store(
            store_id,
            product_type=parsed_type,
            category_id=parsed_category,
            subcategory_id=parsed_subcategory,
            search=search,
        )

        def serialize_page(page):
            return _product_serializer_data(page, repository)

        return paginate_list(request, products, serialize_page)

    def post(self, request, store_id: int):
        from features.products.application.use_cases.manage_product import (
            CreateProductUseCase,
            CreateServiceUseCase,
        )
        from features.products.infrastructure.repositories import (
            DjangoCategoryRepository,
            DjangoProductRepository,
        )
        from features.products.infrastructure.serializers import (
            CreateProductSerializer,
            CreateServiceSerializer,
            ProductSerializer,
        )
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        item_type = request.data.get("product_type", ProductType.PHYSICAL.value)
        product_repository = DjangoProductRepository()
        category_repository = DjangoCategoryRepository()
        store_repository = DjangoStoreRepository()

        try:
            if item_type == ProductType.SERVICE.value:
                serializer = CreateServiceSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data
                product = CreateServiceUseCase(
                    product_repository,
                    category_repository,
                    store_repository,
                ).execute(
                    CreateServiceDTO(
                        store_id=store_id,
                        owner_id=request.user.id,
                        name=data["name"],
                        price=data["price"],
                        category_id=data.get("category_id"),
                        subcategory_id=data.get("subcategory_id"),
                        description=data.get("description", ""),
                        duration_minutes=data.get("duration_minutes"),
                        dynamic_values=data.get("dynamic_values"),
                    )
                )
            else:
                serializer = CreateProductSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data
                product = CreateProductUseCase(
                    product_repository,
                    category_repository,
                    store_repository,
                ).execute(
                    CreateProductDTO(
                        store_id=store_id,
                        owner_id=request.user.id,
                        name=data["name"],
                        price=data["price"],
                        stock=data.get("stock", 0),
                        category_id=data.get("category_id"),
                        subcategory_id=data.get("subcategory_id"),
                        description=data.get("description", ""),
                        dynamic_values=data.get("dynamic_values"),
                    )
                )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (CategoryNotFoundError, InvalidCategoryHierarchyError, DomainValidationError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            _product_serializer_data(product, product_repository),
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        responses={
            200: ProductDetailSerializer,
            404: DetailErrorSerializer,
        },
    ),
    patch=extend_schema(
        request=UpdateProductSerializer,
        responses={
            200: ProductDetailSerializer,
            400: DetailErrorSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class StoreProductDetailView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, store_id: int, product_id: int):
        from features.products.domain.entities import ProductDetails
        from features.products.infrastructure.repositories import DjangoProductRepository

        product_repository = DjangoProductRepository()
        product = product_repository.get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        details = ProductDetails(
            product=product,
            variants=product_repository.list_variants(product_id),
            ingredients=product_repository.list_ingredients(product_id),
            images=product_repository.list_images(product_id),
        )
        return Response(ProductDetailSerializer(details).data)

    def patch(self, request, store_id: int, product_id: int):
        from features.products.application.dto import (
            ProductIngredientInput,
            ProductVariantInput,
            UpdateProductDTO,
        )
        from features.products.application.use_cases.manage_product import (
            DeactivateProductUseCase,
            UpdateProductStockUseCase,
        )
        from features.products.application.use_cases.update_product import UpdateProductUseCase
        from features.products.infrastructure.repositories import (
            DjangoCategoryRepository,
            DjangoProductRepository,
        )
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        product_repository = DjangoProductRepository()
        store_repository = DjangoStoreRepository()

        try:
            if set(request.data.keys()) == {"stock"}:
                serializer = UpdateStockSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                use_case = UpdateProductStockUseCase(product_repository, store_repository)
                product = use_case.execute(
                    UpdateProductStockDTO(
                        product_id=product_id,
                        owner_id=request.user.id,
                        stock=serializer.validated_data["stock"],
                    )
                )
                if product.store_id != store_id:
                    return Response(
                        {"detail": "El producto no pertenece a este comercio"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                return Response(_product_serializer_data(product, product_repository))

            if request.data.get("is_active") is False and len(request.data) == 1:
                use_case = DeactivateProductUseCase(product_repository, store_repository)
                product = use_case.execute(
                    DeactivateProductDTO(product_id=product_id, owner_id=request.user.id)
                )
                if product.store_id != store_id:
                    return Response(
                        {"detail": "El producto no pertenece a este comercio"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                return Response(_product_serializer_data(product, product_repository))

            serializer = UpdateProductSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            variants = None
            if "variants" in data:
                variants = [
                    ProductVariantInput(
                        name=item["name"],
                        price=item["price"],
                        sort_order=item.get("sort_order", 0),
                    )
                    for item in data["variants"]
                ]

            ingredients = None
            if "ingredients" in data:
                ingredients = [
                    ProductIngredientInput(
                        name=item["name"],
                        is_allergen=item.get("is_allergen", False),
                    )
                    for item in data["ingredients"]
                ]

            details = UpdateProductUseCase(
                product_repository,
                DjangoCategoryRepository(),
                store_repository,
            ).execute(
                UpdateProductDTO(
                    product_id=product_id,
                    owner_id=request.user.id,
                    name=data.get("name"),
                    price=data.get("price"),
                    description=data.get("description"),
                    stock=data.get("stock"),
                    category_id=data.get("category_id"),
                    subcategory_id=data.get("subcategory_id"),
                    duration_minutes=data.get("duration_minutes"),
                    variants=variants,
                    ingredients=ingredients,
                    dynamic_values=data.get("dynamic_values"),
                )
            )
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (
            CategoryNotFoundError,
            InvalidCategoryHierarchyError,
            VariantsNotAllowedError,
            DomainValidationError,
        ) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if details.product.store_id != store_id:
            return Response(
                {"detail": "El producto no pertenece a este comercio"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ProductDetailSerializer(details).data)


@extend_schema_view(
    get=extend_schema(responses={200: CategoryTreeSerializer(many=True)}),
    post=extend_schema(
        request=CreateCategorySerializer,
        responses={201: CategoryResponseSerializer, 400: DetailErrorSerializer},
    ),
)
class StoreCategoryListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMerchant()]
        return [AllowAny()]

    def get(self, request, store_id: int):
        from features.products.infrastructure.repositories import DjangoCategoryRepository
        from features.products.infrastructure.serializers import CategoryTreeSerializer

        repository = DjangoCategoryRepository()
        tree = repository.list_tree_by_store(store_id)
        return Response(CategoryTreeSerializer(tree, many=True).data)

    def post(self, request, store_id: int):
        from features.products.application.use_cases.manage_category import (
            CreateCategoryUseCase,
            CreateSubcategoryUseCase,
        )
        from features.products.infrastructure.repositories import DjangoCategoryRepository
        from features.products.infrastructure.serializers import (
            CreateCategorySerializer,
            CreateSubcategorySerializer,
        )
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        category_repository = DjangoCategoryRepository()
        store_repository = DjangoStoreRepository()

        try:
            parent_id = request.data.get("parent_id")
            if parent_id is not None:
                serializer = CreateSubcategorySerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data
                category = CreateSubcategoryUseCase(
                    category_repository,
                    store_repository,
                ).execute(
                    CreateSubcategoryDTO(
                        store_id=store_id,
                        owner_id=request.user.id,
                        parent_id=data["parent_id"],
                        name=data["name"],
                    )
                )
            else:
                serializer = CreateCategorySerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data
                category = CreateCategoryUseCase(
                    category_repository,
                    store_repository,
                ).execute(
                    CreateCategoryDTO(
                        store_id=store_id,
                        owner_id=request.user.id,
                        name=data["name"],
                    )
                )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (CategoryNotFoundError, InvalidCategoryHierarchyError, DomainValidationError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "id": category.id,
                "name": category.name,
                "store_id": category.store_id,
                "parent_id": category.parent_id,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    patch=extend_schema(
        request=UpdateCategorySerializer,
        responses={
            200: CategoryResponseSerializer,
            400: DetailErrorSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
    delete=extend_schema(
        responses={
            204: None,
            400: DetailErrorSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class StoreCategoryDetailView(APIView):
    permission_classes = [IsMerchant]

    def patch(self, request, store_id: int, category_id: int):
        from features.products.application.use_cases.manage_category import (
            UpdateCategoryUseCase,
        )
        from features.products.infrastructure.repositories import DjangoCategoryRepository
        from features.products.infrastructure.serializers import UpdateCategorySerializer
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = UpdateCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            category = UpdateCategoryUseCase(
                DjangoCategoryRepository(),
                DjangoStoreRepository(),
            ).execute(
                UpdateCategoryDTO(
                    store_id=store_id,
                    owner_id=request.user.id,
                    category_id=category_id,
                    name=serializer.validated_data["name"],
                    field_config=serializer.validated_data.get("field_config"),
                )
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except CategoryNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (InvalidCategoryHierarchyError, DomainValidationError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "id": category.id,
                "name": category.name,
                "store_id": category.store_id,
                "parent_id": category.parent_id,
                "field_config": category.field_config or {},
            }
        )

    def delete(self, request, store_id: int, category_id: int):
        from features.products.application.use_cases.manage_category import (
            DeleteCategoryUseCase,
        )
        from features.products.application.dto import DeleteCategoryDTO
        from features.products.domain.exceptions import CategoryInUseError
        from features.products.infrastructure.repositories import DjangoCategoryRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        try:
            DeleteCategoryUseCase(
                DjangoCategoryRepository(),
                DjangoStoreRepository(),
            ).execute(
                DeleteCategoryDTO(
                    store_id=store_id,
                    owner_id=request.user.id,
                    category_id=category_id,
                )
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except CategoryNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except CategoryInUseError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
