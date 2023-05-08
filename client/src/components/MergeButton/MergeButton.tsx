import { Button, InputNumber, Slider, Space } from "antd";
import { Key } from "antd/es/table/interface";
import React, { useEffect, useMemo, useState } from "react";
import { Transaction } from "../../models/merger";

type MergeButtonProps = {
  mergeSelection: Key[];
  data: Transaction[];
  onMerge: (sourceId: number, targetId: number, amount: number) => void;
};

export const MergeButton = ({
  mergeSelection,
  data,
  onMerge,
}: MergeButtonProps) => {
  const [value, setValue] = useState<number | null>(0);

  const [source, target] = useMemo(
    () => [
      data.find((transaction) => transaction.id === mergeSelection[0]),
      data.find((transaction) => transaction.id === mergeSelection[1]),
    ],
    [mergeSelection, data]
  );

  const [min, max] = useMemo(() => [0, source?.amount], [source]);

  useEffect(() => {
    if (source) {
      setValue(source.amount);
    } else {
      setValue(null);
    }
  }, [mergeSelection]);

  const handleMergeButton = () => {
    setValue(null);
    onMerge(source!.id, target!.id, value!);
  };

  const onChange = (newValue: number | null) => {
    setValue(newValue);
  };

  const formatMoney = (value?: number) => {
    if (!value) return "";
    return (value / 100).toFixed(2);
  };

  const parseMoney = (value?: string) => {
    if (!value) return 0;
    const numericValue = parseFloat(value);
    const intValue = Math.round(numericValue * 100);
    return isNaN(intValue) ? 0 : intValue;
  };

  return (
    <Space>
      <Slider
        min={min}
        max={max}
        onChange={onChange}
        value={typeof value === "number" ? value : 0}
        style={{ width: 200 }}
        tooltip={{ formatter: formatMoney }}
      />
      <InputNumber
        value={value}
        min={min}
        max={max}
        onChange={onChange}
        formatter={formatMoney}
        parser={parseMoney}
      />
      <Button
        type="primary"
        onClick={() => {
          handleMergeButton();
        }}
      >
        Merge
      </Button>
    </Space>
  );
};
