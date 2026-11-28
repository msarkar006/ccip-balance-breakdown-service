import { Pagination as CarbonPagination } from '@carbon/react';

interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onChange: (next: { limit: number; offset: number }) => void;
  pageSizes?: number[];
}

/** Offset/limit paging over the API's `{items,total,limit,offset}` lists. */
export function Pagination({ total, limit, offset, onChange, pageSizes = [10, 25, 50] }: PaginationProps) {
  const sizes = pageSizes.includes(limit) ? pageSizes : [...pageSizes, limit].sort((a, b) => a - b);
  return (
    <CarbonPagination
      page={Math.floor(offset / limit) + 1}
      pageSize={limit}
      pageSizes={sizes}
      totalItems={total}
      itemsPerPageText="Records per page"
      onChange={({ page, pageSize }: { page: number; pageSize: number }) =>
        onChange({ limit: pageSize, offset: pageSize === limit ? (page - 1) * pageSize : 0 })
      }
    />
  );
}
