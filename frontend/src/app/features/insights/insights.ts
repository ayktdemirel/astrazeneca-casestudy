import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { InsightsService, Insight } from '../../core/services/insights.service';
import { AuthService } from '../../core/services/auth.service';
import { InsightDetailDialogComponent } from './insight-detail-dialog';
import { InsightFormDialogComponent } from './insight-form-dialog';

@Component({
  selector: 'app-insights',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatDialogModule,
    MatSnackBarModule
  ],
  templateUrl: './insights.html',
  styleUrl: './insights.scss'
})
export class InsightsComponent implements OnInit {
  displayedColumns: string[] = ['title', 'area', 'score', 'date', 'actions'];
  dataSource: Insight[] = [];
  loading = true;

  constructor(
    private insightsService: InsightsService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    private snackBar: MatSnackBar,
    private zone: NgZone,
    private cdr: ChangeDetectorRef,
    private authService: AuthService
  ) { }

  get isAdmin(): boolean {
    return this.authService.isAdmin;
  }

  ngOnInit() {
    this.loadInsights();
  }

  loadInsights() {
    this.insightsService.getInsights().subscribe({
      next: (data) => {
        this.zone.run(() => {
          this.dataSource = data;
          this.loading = false;
          this.cdr.detectChanges();

          // Check for ?id= query param (from notification click)
          this.route.queryParams.subscribe(params => {
            if (params['id']) {
              this.openInsightById(params['id']);
            }
          });
        });
      },
      error: (err) => {
        this.zone.run(() => {
          console.error('InsightsComponent: Error', err);
          this.dataSource = [];
          this.loading = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  openInsightById(id: string) {
    const found = this.dataSource.find(i => i.id === id);
    if (found) {
      this.openInsightDialog(found);
      return;
    }
    this.insightsService.getInsight(id).subscribe({
      next: (insight) => this.openInsightDialog(insight),
      error: (err) => console.error('Could not load insight:', err)
    });
  }

  openInsightDialog(insight: any) {
    this.dialog.open(InsightDetailDialogComponent, {
      data: insight,
      width: '600px',
      maxWidth: '90vw',
      maxHeight: '85vh',
      autoFocus: false,
      position: { top: '80px' }
    });
  }

  openAddDialog() {
    const dialogRef = this.dialog.open(InsightFormDialogComponent, {
      width: '550px',
      maxWidth: '90vw',
      autoFocus: false
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result && result.mode === 'create') {
        this.insightsService.createInsight(result).subscribe({
          next: () => {
            this.snackBar.open('Insight created successfully!', 'Close', { duration: 3000 });
            this.loadInsights();
          },
          error: (err) => {
            if (err.status === 403) {
              this.snackBar.open('You are not authorized to perform this operation.', 'Close', { duration: 5000 });
            } else {
              this.snackBar.open('Failed to create insight: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
            }
          }
        });
      }
    });
  }

  editInsight(insight: Insight) {
    const titleCase = (s: string) => s ? s.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ') : '';

    const dialogRef = this.dialog.open(InsightFormDialogComponent, {
      width: '550px',
      maxWidth: '90vw',
      autoFocus: false,
      data: {
        mode: 'edit',
        insight: {
          id: insight.id,
          title: insight.title,
          description: insight.description || insight.content || '',
          category: titleCase(insight.category || ''),
          therapeuticArea: titleCase(insight.therapeuticArea || ''),
          impactLevel: titleCase(insight.impactLevel || ''),
          relevanceScore: insight.relevanceScore,
          source: insight.source || '',
          competitorId: insight.competitorId || ''
        }
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result && result.mode === 'edit') {
        this.insightsService.updateInsight(insight.id, result).subscribe({
          next: () => {
            this.snackBar.open('Insight updated successfully!', 'Close', { duration: 3000 });
            this.loadInsights();
          },
          error: (err) => {
            if (err.status === 403) {
              this.snackBar.open('You are not authorized to perform this operation.', 'Close', { duration: 5000 });
            } else {
              this.snackBar.open('Failed to update insight: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
            }
          }
        });
      }
    });
  }

  deleteInsight(insight: Insight) {
    if (!confirm(`Delete insight "${insight.title}"?`)) return;

    this.insightsService.deleteInsight(insight.id).subscribe({
      next: () => {
        this.snackBar.open('Insight deleted.', 'Close', { duration: 3000 });
        this.loadInsights();
      },
      error: (err) => {
        if (err.status === 403) {
          this.snackBar.open('You are not authorized to perform this operation.', 'Close', { duration: 5000 });
        } else {
          this.snackBar.open('Failed to delete: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
        }
      }
    });
  }

  getScoreColor(score: number): string {
    if (score >= 8) return 'bg-red-100 text-red-800';
    if (score >= 5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  }
}
