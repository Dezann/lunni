import { DataType, EntryTable } from "../../components/EntryTable";
import React, { useEffect, useState } from "react";
import { FileUploadModal } from "../../components/FileUpload";
import { useGetTransactions } from "../../hooks/merger/useGetTransactions";
import { MergeButton } from "../../components/MergeButton";
import { Key } from "antd/es/table/interface";
import { useMergeMutations } from "../../hooks/merger/useMergeTransactions";
import { RematchCategoriesButton } from "../../components/RematchCategoriesButton";
import { CategoryAddDrawer } from "../../components/CategoryAddDrawer";
import { Space } from "antd";
import { TransactionPartial } from "../../api/merger";
import { useUpdateTransaction } from "../../hooks/merger/useUpdateTransaction";
import { ExportButton } from "../../components/ExportButton";

export const MergerPage = () => {
  const [mergeSelection, setMergeSelection] = useState<Key[]>([]);
  const [pagination, setPagination] = useState<{
    page: number;
    pageSize: number;
  }>({ page: 1, pageSize: 50 });
  const mergeTransactions = useMergeMutations();
  const { data, isLoading: isGetTransactionsLoading } = useGetTransactions(
    pagination.page,
    pagination.pageSize
  );

  const handleMerge = (sourceId: number, targetId: number, amount: number) => {
    mergeTransactions.mutate({
      from_transaction: sourceId,
      to_transaction: targetId,
      amount: amount * 1,
    });
  };

  const [categoryAddRecord, setCategoryAddRecord] = useState<DataType>();
  const { mutate: updateTransaction } = useUpdateTransaction();
  const onCategoryAdd = (record: DataType) => {
    setCategoryAddRecord(record);
  };

  const onRecordUpdate = (transactionPartial: TransactionPartial) => {
    updateTransaction(transactionPartial);
  };

  useEffect(() => {
    mergeTransactions.isSuccess && setMergeSelection([]);
  }, [mergeTransactions.isSuccess]);

  return (
    <div style={{ padding: "16px" }}>
      <CategoryAddDrawer
        record={categoryAddRecord}
        onClose={() => setCategoryAddRecord(undefined)}
      />

      <Space style={{ marginBottom: "16px" }}>
        <FileUploadModal />

        <RematchCategoriesButton />

        <ExportButton />
      </Space>

      <EntryTable
        isLoading={isGetTransactionsLoading || mergeTransactions.isLoading}
        totalEntries={data?.count}
        data={data?.results || []}
        mergeSelection={mergeSelection}
        onMergeSelectionChange={setMergeSelection}
        onPaginationChange={(page, pageSize) =>
          setPagination({ page, pageSize })
        }
        onCategoryAdd={onCategoryAdd}
        onRecordUpdate={onRecordUpdate}
        mergeComponent={() => (
          <Space>
            <MergeButton
              mergeSelection={mergeSelection}
              data={data?.results || []}
              onMerge={handleMerge}
            />
          </Space>
        )}
      />
    </div>
  );
};
