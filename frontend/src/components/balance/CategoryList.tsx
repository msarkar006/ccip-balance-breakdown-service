import { Accordion, AccordionItem, Stack } from '@carbon/react';
import { BalanceCategory } from '../../types/balance';
import { formatCurrency, formatDate } from '../../lib/utils';
import styles from './CategoryList.module.scss';

interface CategoryListProps {
  categories: BalanceCategory[];
}

export function CategoryList({ categories }: CategoryListProps) {
  if (categories.length === 0) {
    return null;
  }

  const getCategoryLabel = (name: string): string => {
    const labels: Record<string, string> = {
      StandardPurchase: 'Standard purchases',
      PromotionalPurchase: 'Purchase promotion',
      BalanceTransfer: 'Balance transfer',
      Instalment: 'Instalment plan',
    };
    return labels[name] || name;
  };

  const getPromotionalTiming = (category: BalanceCategory): string => {
    if (!category.promo_rate && !category.promo_end_date) {
      return 'None';
    }

    if (!category.promo_end_date) {
      return 'Fixed plan, no end date shown for the rate';
    }

    const endDate = new Date(category.promo_end_date);
    const now = new Date();
    const daysLeft = Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    return `Ends ${formatDate(category.promo_end_date)} (${daysLeft} days left), then ${category.apr}%`;
  };

  return (
    <Accordion>
      {categories.map((category, index) => (
        <AccordionItem
          key={category.id}
          title={
            <div className={styles.accordionTitle}>
              <span>
                {index + 1}. {getCategoryLabel(category.category_name)}
              </span>
              <span className={styles.amount}>{formatCurrency(parseFloat(category.category_amount))}</span>
            </div>
          }
        >
          <Stack gap={5}>
            <div className={styles.detail}>
              <div className={styles.label}>Interest rate (APR)</div>
              <div>{category.apr}%</div>
            </div>
            <div className={styles.detail}>
              <div className={styles.label}>Promotional timing</div>
              <div>{getPromotionalTiming(category)}</div>
            </div>
            {category.source_link && (
              <div className={styles.detail}>
                <div className={styles.label}>Linked to</div>
                <div>
                  {category.source_link.source_reference} · {category.source_link.source_type}
                </div>
              </div>
            )}
          </Stack>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
