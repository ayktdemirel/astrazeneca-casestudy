import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { Insight } from '../../core/services/insights.service';

@Component({
  selector: 'app-insight-detail-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule
  ],
  template: `
    <div class="p-4 overflow-hidden">
      <div class="flex items-start justify-between gap-3 mb-4">
        <h2 class="text-xl font-bold text-gray-800 m-0" style="overflow-wrap: break-word; word-break: break-word; white-space: normal;">{{ data.title }}</h2>
        <button mat-icon-button (click)="close()" class="flex-shrink-0 -mt-1 -mr-2">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <mat-dialog-content class="max-h-[70vh]">
        <div class="space-y-4">
          <!-- Meta chips -->
          <div class="flex flex-wrap gap-2">
            <span *ngIf="data.category"
              class="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700">
              {{ data.category }}
            </span>
            <span *ngIf="data.therapeuticArea"
              class="px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-700">
              {{ data.therapeuticArea }}
            </span>
            <span *ngIf="data.impactLevel"
              class="px-3 py-1 rounded-full text-xs font-semibold"
              [ngClass]="{
                'bg-red-100 text-red-700': data.impactLevel === 'High',
                'bg-yellow-100 text-yellow-700': data.impactLevel === 'Medium',
                'bg-blue-100 text-blue-700': data.impactLevel === 'Low'
              }">
              {{ data.impactLevel }} Impact
            </span>
            <span *ngIf="data.relevanceScore != null"
              class="px-3 py-1 rounded-full text-xs font-bold"
              [ngClass]="{
                'bg-red-100 text-red-800': data.relevanceScore >= 8,
                'bg-yellow-100 text-yellow-800': data.relevanceScore >= 5 && data.relevanceScore < 8,
                'bg-blue-100 text-blue-800': data.relevanceScore < 5
              }">
              Score: {{ data.relevanceScore }}/10
            </span>
          </div>

          <!-- Description / Content -->
          <div class="bg-gray-50 rounded-lg p-4">
            <p class="text-gray-700 whitespace-pre-line leading-relaxed">{{ data.description || data.content }}</p>
          </div>

          <!-- Source info -->
          <div class="text-sm text-gray-500 space-y-1">
            <p *ngIf="data.source"><strong>Source:</strong> {{ data.source }}</p>
            <p *ngIf="data.publishedDate"><strong>Published:</strong> {{ data.publishedDate | date:'mediumDate' }}</p>
            <p *ngIf="data.createdAt"><strong>Added:</strong> {{ data.createdAt | date:'medium' }}</p>
          </div>
        </div>
      </mat-dialog-content>

      <mat-dialog-actions align="end" class="mt-4">
        <button mat-button (click)="close()">Close</button>
      </mat-dialog-actions>
    </div>
  `
})
export class InsightDetailDialogComponent {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private dialogRef: MatDialogRef<InsightDetailDialogComponent>
  ) { }

  close() {
    this.dialogRef.close();
  }
}
