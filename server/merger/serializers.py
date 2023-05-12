from rest_framework import serializers

from merger.models import TransactionLog, TransactionLogMerge, TransactionCategory, TransactionCategoryMatcher


class TransactionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionCategory
        fields = ['id', 'name', 'variant']


class TransactionCategoryMatcherSerializer(serializers.ModelSerializer):
    category = TransactionCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(source='category', queryset=TransactionCategory.objects.all())

    class Meta:
        model = TransactionCategoryMatcher
        fields = ['id', 'regex_expression', 'category', 'category_id']


class TransactionLogSerializer(serializers.ModelSerializer):
    calculated_amount = serializers.SerializerMethodField()
    category = TransactionCategorySerializer()

    class Meta:
        model = TransactionLog
        fields = ['id', 'date', 'description', 'note', 'account', 'category', 'amount', 'calculated_amount']
        read_only_fields = ['id', 'date', 'description', 'account', 'category', 'amount', 'calculated_amount']

    @staticmethod
    def get_calculated_amount(instance):
        return instance.calculated_amount


class TransactionLogExportSerializer(TransactionLogSerializer):
    calculated_amount = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = TransactionLog
        fields = ['id', 'date', 'description', 'note', 'account', 'category_name', 'amount', 'calculated_amount']
        read_only_fields = ['id', 'date', 'description', 'account', 'category_name', 'amount', 'calculated_amount']

    @staticmethod
    def get_calculated_amount(instance):
        return instance.calculated_amount

    @staticmethod
    def get_category_name(instance):
        if instance.category is not None:
            return instance.category.name


class TransactionLogMergeSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField(
        min_value=0,
    )

    def validate(self, data):
        from_transaction = data.get('from_transaction')

        attempted_amount_transfer = data.get('amount')
        available_amount = getattr(from_transaction, 'amount')

        if attempted_amount_transfer <= 0:
            raise serializers.ValidationError(
                'Cannot transfer negative amount')

        if attempted_amount_transfer > available_amount:
            raise serializers.ValidationError(
                'Cannot transfer from transaction more than the available transaction value')

        return data

    class Meta:
        model = TransactionLogMerge
        fields = ['from_transaction', 'to_transaction', 'amount']
